"""
Docker service for managing browser containers
"""
import docker
import secrets
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class DockerService:
    """Service for managing Docker containers for browser sessions"""
    
    def __init__(self):
        self.client = None
        self._network_name = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Docker client"""
        try:
            docker_host = current_app.config.get('DOCKER_HOST', 'unix:///var/run/docker.sock')
            if docker_host.startswith('unix://'):
                self.client = docker.DockerClient(base_url=docker_host)
            else:
                self.client = docker.from_env()
            
            # Test connection
            self.client.ping()
            logger.info("Docker client initialized successfully")
            
            # Initialize network
            self._initialize_network()
            
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            self.client = None
    
    def _initialize_network(self):
        """Initialize or create Docker network for browser containers"""
        self._network_name = current_app.config.get('DOCKER_NETWORK', 'cloud-browser-network')
        
        try:
            # Try to get existing network
            try:
                network = self.client.networks.get(self._network_name)
                logger.info(f"Using existing Docker network: {self._network_name}")
            except docker.errors.NotFound:
                # Create new network
                network = self.client.networks.create(
                    self._network_name,
                    driver="bridge",
                    options={
                        "com.docker.network.bridge.enable_ip_masquerade": "true",
                        "com.docker.network.bridge.enable_icc": "false"
                    }
                )
                logger.info(f"Created Docker network: {self._network_name}")
                
        except Exception as e:
            logger.error(f"Failed to initialize Docker network: {e}")
            self._network_name = None
    
    def is_available(self) -> bool:
        """Check if Docker service is available"""
        try:
            if self.client:
                self.client.ping()
                return True
        except Exception:
            pass
        return False
    
    def create_browser_container(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new browser container
        
        Args:
            session_data: Dictionary containing session configuration
            
        Returns:
            Dictionary with container information
        """
        if not self.is_available():
            raise Exception("Docker service is not available")
        
        try:
            # Extract configuration
            browser_type = session_data.get('browser_type', 'firefox')
            user_id = session_data.get('user_id')
            screen_resolution = session_data.get('screen_resolution', '1920x1080')
            
            # Get Docker image based on browser type
            image_name = self._get_browser_image(browser_type)
            
            # Generate unique container name and VNC password
            container_name = f"browser-{browser_type}-{user_id}-{int(time.time())}"
            vnc_password = secrets.token_urlsafe(6)[:8]  # VNC passwords are limited to 8 chars
            
            # Find available ports
            vnc_port = self._find_available_port(5900, 6000)
            web_port = self._find_available_port(6080, 7000)
            
            # Container environment variables
            environment = {
                'VNC_PW': vnc_password,
                'RESOLUTION': screen_resolution,
                'VNC_PORT': str(vnc_port),
                'VNC_RESOLUTION': screen_resolution,
                'VNC_COL_DEPTH': '24',
                'NOVNC_PORT': str(web_port),
                'DISPLAY': ':1',
                'USER': 'kasm-user'
            }
            
            # Add any custom environment variables
            custom_env = session_data.get('environment_vars', {})
            environment.update(custom_env)
            
            # Resource limits
            cpu_limit = session_data.get('cpu_limit', current_app.config['CONTAINER_CPU_LIMIT'])
            memory_limit = session_data.get('memory_limit', current_app.config['CONTAINER_MEMORY_LIMIT'])
            
            # Container configuration
            container_config = {
                'image': image_name,
                'name': container_name,
                'environment': environment,
                'ports': {
                    '5901/tcp': vnc_port,  # VNC port
                    '6901/tcp': web_port   # noVNC web port
                },
                'shm_size': '2g',  # Shared memory for browser
                'security_opt': ['seccomp=unconfined'],  # Allow browser to run
                'mem_limit': memory_limit,
                'cpu_quota': int(cpu_limit * 100000),  # CPU quota in microseconds
                'cpu_period': 100000,
                'restart_policy': {'Name': 'no'},
                'labels': {
                    'service': 'cloud-browser',
                    'user_id': str(user_id),
                    'browser_type': browser_type,
                    'created_at': datetime.utcnow().isoformat()
                }
            }
            
            # Add to network if available
            if self._network_name:
                container_config['network'] = self._network_name
            
            # Create and start container
            container = self.client.containers.run(
                detach=True,
                **container_config
            )
            
            # Wait for container to be ready
            self._wait_for_container_ready(container, timeout=60)
            
            # Generate access URLs
            host = 'localhost'  # In production, this would be the actual host
            access_url = f"http://{host}:{web_port}"
            vnc_url = f"vnc://{host}:{vnc_port}"
            
            container_info = {
                'container_id': container.id,
                'container_name': container_name,
                'docker_image': image_name,
                'vnc_port': vnc_port,
                'web_port': web_port,
                'vnc_password': vnc_password,
                'access_url': access_url,
                'vnc_url': vnc_url,
                'status': 'running',
                'created_at': datetime.utcnow(),
                'environment': environment
            }
            
            logger.info(f"Created browser container {container_name} for user {user_id}")
            return container_info
            
        except Exception as e:
            logger.error(f"Failed to create browser container: {e}")
            raise Exception(f"Failed to create browser container: {str(e)}")
    
    def _get_browser_image(self, browser_type: str) -> str:
        """Get Docker image name for browser type"""
        images = {
            'firefox': current_app.config.get('FIREFOX_IMAGE', 'kasmweb/firefox:1.14.0'),
            'chrome': current_app.config.get('CHROME_IMAGE', 'kasmweb/chrome:1.14.0'),
            'chromium': current_app.config.get('CHROME_IMAGE', 'kasmweb/chrome:1.14.0')
        }
        
        return images.get(browser_type, images['firefox'])
    
    def _find_available_port(self, start_port: int, end_port: int) -> int:
        """Find an available port in the given range"""
        import socket
        
        for port in range(start_port, end_port):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.bind(('localhost', port))
                    return port
            except OSError:
                continue
        
        raise Exception(f"No available ports in range {start_port}-{end_port}")
    
    def _wait_for_container_ready(self, container, timeout: int = 60):
        """Wait for container to be ready"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                container.reload()
                if container.status == 'running':
                    # Additional check: ensure VNC service is ready
                    logs = container.logs(tail=50).decode('utf-8')
                    if 'VNC started' in logs or 'noVNC started' in logs:
                        return True
                    
                    # Wait a bit more for services to start
                    time.sleep(2)
                    return True
                    
            except Exception as e:
                logger.warning(f"Error checking container readiness: {e}")
            
            time.sleep(1)
        
        raise Exception(f"Container not ready after {timeout} seconds")
    
    def stop_container(self, container_id: str, timeout: int = 10) -> bool:
        """Stop a browser container"""
        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=timeout)
            logger.info(f"Stopped container {container_id}")
            return True
            
        except docker.errors.NotFound:
            logger.warning(f"Container {container_id} not found")
            return True  # Already gone
            
        except Exception as e:
            logger.error(f"Failed to stop container {container_id}: {e}")
            return False
    
    def remove_container(self, container_id: str, force: bool = False) -> bool:
        """Remove a browser container"""
        try:
            container = self.client.containers.get(container_id)
            container.remove(force=force)
            logger.info(f"Removed container {container_id}")
            return True
            
        except docker.errors.NotFound:
            logger.warning(f"Container {container_id} not found")
            return True  # Already gone
            
        except Exception as e:
            logger.error(f"Failed to remove container {container_id}: {e}")
            return False
    
    def get_container_status(self, container_id: str) -> Dict[str, Any]:
        """Get container status and information"""
        try:
            container = self.client.containers.get(container_id)
            container.reload()
            
            # Get container stats
            stats = container.stats(stream=False)
            
            # Calculate CPU usage
            cpu_usage = 0
            if 'cpu_stats' in stats and 'precpu_stats' in stats:
                cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                           stats['precpu_stats']['cpu_usage']['total_usage']
                system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                              stats['precpu_stats']['system_cpu_usage']
                
                if system_delta > 0:
                    cpu_usage = (cpu_delta / system_delta) * 100
            
            # Calculate memory usage
            memory_usage = 0
            memory_limit = 0
            if 'memory_stats' in stats:
                memory_usage = stats['memory_stats'].get('usage', 0)
                memory_limit = stats['memory_stats'].get('limit', 0)
            
            return {
                'status': container.status,
                'created': container.attrs['Created'],
                'started_at': container.attrs['State'].get('StartedAt'),
                'cpu_usage_percent': round(cpu_usage, 2),
                'memory_usage_bytes': memory_usage,
                'memory_limit_bytes': memory_limit,
                'memory_usage_percent': round((memory_usage / memory_limit * 100) if memory_limit else 0, 2),
                'network_rx_bytes': stats.get('networks', {}).get('eth0', {}).get('rx_bytes', 0),
                'network_tx_bytes': stats.get('networks', {}).get('eth0', {}).get('tx_bytes', 0),
                'is_running': container.status == 'running'
            }
            
        except docker.errors.NotFound:
            return {
                'status': 'not_found',
                'is_running': False
            }
            
        except Exception as e:
            logger.error(f"Failed to get container status for {container_id}: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'is_running': False
            }
    
    def list_user_containers(self, user_id: int) -> List[Dict[str, Any]]:
        """List all containers for a specific user"""
        try:
            containers = self.client.containers.list(
                all=True,
                filters={'label': f'user_id={user_id}'}
            )
            
            container_list = []
            for container in containers:
                container_info = {
                    'container_id': container.id,
                    'name': container.name,
                    'status': container.status,
                    'created': container.attrs['Created'],
                    'image': container.image.tags[0] if container.image.tags else 'unknown',
                    'labels': container.labels
                }
                container_list.append(container_info)
            
            return container_list
            
        except Exception as e:
            logger.error(f"Failed to list containers for user {user_id}: {e}")
            return []
    
    def cleanup_expired_containers(self, max_age_hours: int = 24) -> int:
        """Clean up old/expired containers"""
        cleaned_count = 0
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        try:
            # Get all cloud-browser containers
            containers = self.client.containers.list(
                all=True,
                filters={'label': 'service=cloud-browser'}
            )
            
            for container in containers:
                try:
                    created_time = datetime.fromisoformat(
                        container.attrs['Created'].replace('Z', '+00:00')
                    )
                    
                    if created_time < cutoff_time:
                        logger.info(f"Cleaning up expired container: {container.name}")
                        self.remove_container(container.id, force=True)
                        cleaned_count += 1
                        
                except Exception as e:
                    logger.error(f"Error cleaning up container {container.id}: {e}")
            
            logger.info(f"Cleaned up {cleaned_count} expired containers")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired containers: {e}")
            return 0
    
    def get_system_resources(self) -> Dict[str, Any]:
        """Get Docker system resource information"""
        try:
            info = self.client.info()
            version = self.client.version()
            
            return {
                'docker_version': version.get('Version', 'unknown'),
                'containers_running': info.get('ContainersRunning', 0),
                'containers_total': info.get('Containers', 0),
                'images_count': info.get('Images', 0),
                'memory_total': info.get('MemTotal', 0),
                'cpu_count': info.get('NCPU', 0),
                'storage_driver': info.get('Driver', 'unknown'),
                'kernel_version': info.get('KernelVersion', 'unknown'),
                'operating_system': info.get('OperatingSystem', 'unknown'),
                'server_version': info.get('ServerVersion', 'unknown')
            }
            
        except Exception as e:
            logger.error(f"Failed to get system resources: {e}")
            return {}
    
    def pull_browser_images(self) -> Dict[str, bool]:
        """Pull/update browser images"""
        results = {}
        
        images = {
            'firefox': current_app.config.get('FIREFOX_IMAGE', 'kasmweb/firefox:1.14.0'),
            'chrome': current_app.config.get('CHROME_IMAGE', 'kasmweb/chrome:1.14.0')
        }
        
        for browser_type, image_name in images.items():
            try:
                logger.info(f"Pulling image: {image_name}")
                self.client.images.pull(image_name)
                results[browser_type] = True
                logger.info(f"Successfully pulled {image_name}")
                
            except Exception as e:
                logger.error(f"Failed to pull {image_name}: {e}")
                results[browser_type] = False
        
        return results

# Global Docker service instance
docker_service = DockerService()

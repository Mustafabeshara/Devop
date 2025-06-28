import { Fragment } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { Dialog, Transition } from '@headlessui/react'
import {
  HomeIcon,
  WindowIcon,
  CodeBracketIcon,
  UserIcon,

  XMarkIcon,
  ShieldCheckIcon,
} from '@heroicons/react/24/outline'
import { useAuth } from '../../hooks/useAuth'
import clsx from 'clsx'

interface SidebarProps {
  open: boolean
  onClose: () => void
  isMobile: boolean
}

export function Sidebar({ open, onClose, isMobile }: SidebarProps) {
  const { user } = useAuth()
  const location = useLocation()

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
    { name: 'Browser Sessions', href: '/sessions', icon: WindowIcon },
    { name: 'Code Analysis', href: '/code', icon: CodeBracketIcon },
    { name: 'Profile', href: '/profile', icon: UserIcon },
  ]

  // Add admin navigation for admin users
  if (user?.is_admin) {
    navigation.push({ name: 'Admin Panel', href: '/admin', icon: ShieldCheckIcon })
  }

  const SidebarContent = () => (
    <div className="flex h-full flex-col bg-white shadow-xl">
      {/* Logo and brand */}
      <div className="flex h-16 shrink-0 items-center px-6 border-b border-gray-200">
        <div className="flex items-center">
          <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-lg flex items-center justify-center">
            <WindowIcon className="w-5 h-5 text-white" />
          </div>
          <span className="ml-3 text-lg font-semibold text-gray-900">
            Cloud Browser
          </span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 bg-white px-3 py-6">
        {navigation.map((item) => {
          const isActive = location.pathname.startsWith(item.href)
          return (
            <NavLink
              key={item.name}
              to={item.href}
              onClick={isMobile ? onClose : undefined}
              className={clsx(
                'group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors duration-200',
                isActive
                  ? 'bg-primary-50 text-primary-700 border-r-2 border-primary-500'
                  : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
              )}
            >
              <item.icon
                className={clsx(
                  'mr-3 h-5 w-5 transition-colors duration-200',
                  isActive
                    ? 'text-primary-500'
                    : 'text-gray-400 group-hover:text-gray-500'
                )}
                aria-hidden="true"
              />
              {item.name}
            </NavLink>
          )
        })}
      </nav>

      {/* User info */}
      <div className="flex-shrink-0 border-t border-gray-200 p-4">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
              <UserIcon className="w-5 h-5 text-gray-600" />
            </div>
          </div>
          <div className="ml-3 min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">
              {user?.full_name || user?.username}
            </p>
            <p className="text-xs text-gray-500 truncate">
              {user?.email}
            </p>
          </div>
        </div>
      </div>
    </div>
  )

  if (isMobile) {
    return (
      <Transition.Root show={open} as={Fragment}>
        <Dialog as="div" className="relative z-50 lg:hidden" onClose={onClose}>
          <Transition.Child
            as={Fragment}
            enter="transition-opacity ease-linear duration-300"
            enterFrom="opacity-0"
            enterTo="opacity-100"
            leave="transition-opacity ease-linear duration-300"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
          >
            <div className="fixed inset-0 bg-gray-900/80" />
          </Transition.Child>

          <div className="fixed inset-0 flex">
            <Transition.Child
              as={Fragment}
              enter="transition ease-in-out duration-300 transform"
              enterFrom="-translate-x-full"
              enterTo="translate-x-0"
              leave="transition ease-in-out duration-300 transform"
              leaveFrom="translate-x-0"
              leaveTo="-translate-x-full"
            >
              <Dialog.Panel className="relative mr-16 flex w-full max-w-xs flex-1">
                <Transition.Child
                  as={Fragment}
                  enter="ease-in-out duration-300"
                  enterFrom="opacity-0"
                  enterTo="opacity-100"
                  leave="ease-in-out duration-300"
                  leaveFrom="opacity-100"
                  leaveTo="opacity-0"
                >
                  <div className="absolute left-full top-0 flex w-16 justify-center pt-5">
                    <button type="button" className="-m-2.5 p-2.5" onClick={onClose}>
                      <span className="sr-only">Close sidebar</span>
                      <XMarkIcon className="h-6 w-6 text-white" aria-hidden="true" />
                    </button>
                  </div>
                </Transition.Child>
                <SidebarContent />
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </Dialog>
      </Transition.Root>
    )
  }

  return <SidebarContent />
}

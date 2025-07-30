import { useState } from 'react'
import { Switch } from '@headlessui/react'
import toast from 'react-hot-toast'

function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(' ')
}

export function SettingsPage() {
  const [settings, setSettings] = useState({
    emailNotifications: true,
    autoProcessing: true,
    darkMode: false,
    compressionQuality: 'high',
    retentionDays: 30,
  })

  const handleSave = () => {
    // Save settings to backend
    toast.success('Settings saved successfully')
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">Settings</h1>

      <div className="mt-6 space-y-6">
        {/* Notifications */}
        <div className="rounded-lg bg-white shadow dark:bg-gray-800">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
              Notifications
            </h3>
            <div className="mt-6 space-y-6">
              <Switch.Group as="div" className="flex items-center justify-between">
                <span className="flex flex-grow flex-col">
                  <Switch.Label
                    as="span"
                    className="text-sm font-medium text-gray-900 dark:text-white"
                  >
                    Email notifications
                  </Switch.Label>
                  <Switch.Description
                    as="span"
                    className="text-sm text-gray-500 dark:text-gray-400"
                  >
                    Receive email notifications when processing is complete
                  </Switch.Description>
                </span>
                <Switch
                  checked={settings.emailNotifications}
                  onChange={(value) => setSettings({ ...settings, emailNotifications: value })}
                  className={classNames(
                    settings.emailNotifications ? 'bg-indigo-600' : 'bg-gray-200 dark:bg-gray-700',
                    'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:outline-none'
                  )}
                >
                  <span
                    aria-hidden="true"
                    className={classNames(
                      settings.emailNotifications ? 'translate-x-5' : 'translate-x-0',
                      'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out'
                    )}
                  />
                </Switch>
              </Switch.Group>
            </div>
          </div>
        </div>

        {/* Processing */}
        <div className="rounded-lg bg-white shadow dark:bg-gray-800">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
              Processing
            </h3>
            <div className="mt-6 space-y-6">
              <Switch.Group as="div" className="flex items-center justify-between">
                <span className="flex flex-grow flex-col">
                  <Switch.Label
                    as="span"
                    className="text-sm font-medium text-gray-900 dark:text-white"
                  >
                    Auto-processing
                  </Switch.Label>
                  <Switch.Description
                    as="span"
                    className="text-sm text-gray-500 dark:text-gray-400"
                  >
                    Automatically process uploaded files
                  </Switch.Description>
                </span>
                <Switch
                  checked={settings.autoProcessing}
                  onChange={(value) => setSettings({ ...settings, autoProcessing: value })}
                  className={classNames(
                    settings.autoProcessing ? 'bg-indigo-600' : 'bg-gray-200 dark:bg-gray-700',
                    'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:outline-none'
                  )}
                >
                  <span
                    aria-hidden="true"
                    className={classNames(
                      settings.autoProcessing ? 'translate-x-5' : 'translate-x-0',
                      'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out'
                    )}
                  />
                </Switch>
              </Switch.Group>

              <div>
                <label className="text-sm font-medium text-gray-900 dark:text-white">
                  Compression Quality
                </label>
                <select
                  value={settings.compressionQuality}
                  onChange={(e) => setSettings({ ...settings, compressionQuality: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 py-2 pr-10 pl-3 text-base focus:border-indigo-500 focus:ring-indigo-500 focus:outline-none sm:text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                >
                  <option value="low">Low (faster processing)</option>
                  <option value="medium">Medium</option>
                  <option value="high">High (better quality)</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Storage */}
        <div className="rounded-lg bg-white shadow dark:bg-gray-800">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">Storage</h3>
            <div className="mt-6">
              <label className="text-sm font-medium text-gray-900 dark:text-white">
                File Retention (days)
              </label>
              <input
                type="number"
                value={settings.retentionDays}
                onChange={(e) =>
                  setSettings({ ...settings, retentionDays: parseInt(e.target.value) })
                }
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                min="1"
                max="365"
              />
              <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                Files older than this will be automatically deleted
              </p>
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end">
          <button
            type="button"
            onClick={handleSave}
            className="inline-flex justify-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:outline-none"
          >
            Save Settings
          </button>
        </div>
      </div>
    </div>
  )
}

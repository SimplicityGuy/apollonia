import { useQuery } from '@tanstack/react-query'
import { api } from '@/services/api'
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

const COLORS = ['#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ef4444']

export function AnalyticsPage() {
  const { data: analytics } = useQuery({
    queryKey: ['analytics'],
    queryFn: async () => {
      const response = await api.get('/analytics')
      return response.data
    },
  })

  const mediaTypeData = [
    { name: 'Video', value: analytics?.media_types?.video || 0 },
    { name: 'Audio', value: analytics?.media_types?.audio || 0 },
    { name: 'Other', value: analytics?.media_types?.other || 0 },
  ]

  const processingData = analytics?.processing_timeline || []
  const storageData = analytics?.storage_growth || []

  return (
    <div>
      <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">Analytics</h1>

      {/* Summary Cards */}
      <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <div className="overflow-hidden rounded-lg bg-white px-4 py-5 shadow dark:bg-gray-800">
          <dt className="truncate text-sm font-medium text-gray-500 dark:text-gray-400">
            Total Files
          </dt>
          <dd className="mt-1 text-3xl font-semibold tracking-tight text-gray-900 dark:text-white">
            {analytics?.total_files || 0}
          </dd>
        </div>
        <div className="overflow-hidden rounded-lg bg-white px-4 py-5 shadow dark:bg-gray-800">
          <dt className="truncate text-sm font-medium text-gray-500 dark:text-gray-400">
            Total Storage
          </dt>
          <dd className="mt-1 text-3xl font-semibold tracking-tight text-gray-900 dark:text-white">
            {formatBytes(analytics?.total_storage || 0)}
          </dd>
        </div>
        <div className="overflow-hidden rounded-lg bg-white px-4 py-5 shadow dark:bg-gray-800">
          <dt className="truncate text-sm font-medium text-gray-500 dark:text-gray-400">
            Processing Rate
          </dt>
          <dd className="mt-1 text-3xl font-semibold tracking-tight text-gray-900 dark:text-white">
            {analytics?.processing_rate || 0}/hr
          </dd>
        </div>
        <div className="overflow-hidden rounded-lg bg-white px-4 py-5 shadow dark:bg-gray-800">
          <dt className="truncate text-sm font-medium text-gray-500 dark:text-gray-400">
            Avg Processing Time
          </dt>
          <dd className="mt-1 text-3xl font-semibold tracking-tight text-gray-900 dark:text-white">
            {analytics?.avg_processing_time || 0}s
          </dd>
        </div>
      </div>

      {/* Charts */}
      <div className="mt-8 grid grid-cols-1 gap-8 lg:grid-cols-2">
        {/* Media Type Distribution */}
        <div className="rounded-lg bg-white p-6 shadow dark:bg-gray-800">
          <h2 className="text-lg font-medium text-gray-900 dark:text-white">
            Media Type Distribution
          </h2>
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={mediaTypeData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {mediaTypeData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Processing Timeline */}
        <div className="rounded-lg bg-white p-6 shadow dark:bg-gray-800">
          <h2 className="text-lg font-medium text-gray-900 dark:text-white">Processing Timeline</h2>
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={processingData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="processed" stroke="#8b5cf6" name="Files Processed" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Storage Growth */}
        <div className="rounded-lg bg-white p-6 shadow dark:bg-gray-800">
          <h2 className="text-lg font-medium text-gray-900 dark:text-white">Storage Growth</h2>
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={storageData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="storage" fill="#3b82f6" name="Storage (GB)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Processing Status */}
        <div className="rounded-lg bg-white p-6 shadow dark:bg-gray-800">
          <h2 className="text-lg font-medium text-gray-900 dark:text-white">Processing Status</h2>
          <div className="mt-4 space-y-4">
            <div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Completed
                </span>
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  {analytics?.status?.completed || 0}
                </span>
              </div>
              <div className="mt-2 h-2 w-full rounded-full bg-gray-200 dark:bg-gray-700">
                <div
                  className="h-2 rounded-full bg-green-500"
                  style={{
                    width: `${
                      ((analytics?.status?.completed || 0) / (analytics?.total_files || 1)) * 100
                    }%`,
                  }}
                />
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Processing
                </span>
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  {analytics?.status?.processing || 0}
                </span>
              </div>
              <div className="mt-2 h-2 w-full rounded-full bg-gray-200 dark:bg-gray-700">
                <div
                  className="h-2 rounded-full bg-yellow-500"
                  style={{
                    width: `${
                      ((analytics?.status?.processing || 0) / (analytics?.total_files || 1)) * 100
                    }%`,
                  }}
                />
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Failed</span>
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  {analytics?.status?.failed || 0}
                </span>
              </div>
              <div className="mt-2 h-2 w-full rounded-full bg-gray-200 dark:bg-gray-700">
                <div
                  className="h-2 rounded-full bg-red-500"
                  style={{
                    width: `${
                      ((analytics?.status?.failed || 0) / (analytics?.total_files || 1)) * 100
                    }%`,
                  }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

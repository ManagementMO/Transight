import { useState, useEffect } from 'react';
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
  ResponsiveContainer
} from 'recharts';

export default function Analytics() {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        console.log('Fetching analytics data...');
        const response = await fetch('http://localhost:8000/api/analytics/overview');

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const analyticsData = await response.json();
        console.log('Analytics data loaded:', analyticsData);
        setData(analyticsData);
      } catch (error) {
        console.error('Failed to load analytics:', error);
        alert(`Failed to load analytics: ${error.message}\n\nPlease restart the backend API server.`);
      } finally {
        setIsLoading(false);
      }
    };

    fetchAnalytics();
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600 font-medium">Loading analytics...</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-gray-500">Failed to load analytics data</p>
      </div>
    );
  }

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316'];

  // Transform hourly data to show AM/PM labels
  const hourlyData = data.delayByHour.map(item => ({
    ...item,
    hourLabel: item.hour === 0 ? '12 AM' : item.hour < 12 ? `${item.hour} AM` : item.hour === 12 ? '12 PM' : `${item.hour - 12} PM`
  }));

  // Day of week heatmap data
  const dayHeatmapData = data.delayByDayOfWeek || [];

  return (
    <div className="h-full overflow-y-auto bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Incidents</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{data.totalIncidents.toLocaleString()}</p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Average Delay</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{data.avgDelay} <span className="text-lg text-gray-500">min</span></p>
              </div>
              <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Most Delayed Route</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{data.topDelayedRoutes[0]?.route || 'N/A'}</p>
              </div>
              <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                </svg>
              </div>
            </div>
          </div>
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Most Delayed Routes */}
          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Most Delayed Routes</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={data.topDelayedRoutes}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="route" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} label={{ value: 'Avg Delay (min)', angle: -90, position: 'insideLeft', style: { fontSize: 12 } }} />
                <Tooltip
                  contentStyle={{ backgroundColor: 'white', border: '1px solid #e5e7eb', borderRadius: '8px' }}
                  formatter={(value, name) => [
                    name === 'avgDelay' ? `${value} min` : value,
                    name === 'avgDelay' ? 'Average Delay' : 'Incidents'
                  ]}
                />
                <Bar dataKey="avgDelay" fill="#3b82f6" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Delay Patterns by Hour */}
          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Delay Patterns by Hour</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={hourlyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis
                  dataKey="hourLabel"
                  tick={{ fontSize: 10 }}
                  interval={2}
                />
                <YAxis tick={{ fontSize: 12 }} label={{ value: 'Avg Delay (min)', angle: -90, position: 'insideLeft', style: { fontSize: 12 } }} />
                <Tooltip
                  contentStyle={{ backgroundColor: 'white', border: '1px solid #e5e7eb', borderRadius: '8px' }}
                  formatter={(value) => [`${value} min`, 'Average Delay']}
                />
                <Line type="monotone" dataKey="avgDelay" stroke="#10b981" strokeWidth={3} dot={{ fill: '#10b981', r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Incident Type Breakdown */}
          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Incident Type Breakdown</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={data.incidentBreakdown}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ type, percentage }) => `${type.length > 15 ? type.substring(0, 12) + '...' : type} (${percentage}%)`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {data.incidentBreakdown.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: 'white', border: '1px solid #e5e7eb', borderRadius: '8px' }}
                  formatter={(value, name, props) => [
                    `${value} incidents (${props.payload.percentage}%)`,
                    props.payload.type
                  ]}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Day of Week Heatmap */}
          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Average Delay by Day of Week</h3>
            <div className="space-y-3 py-4">
              {dayHeatmapData.map((item) => {
                const maxDelay = Math.max(...dayHeatmapData.map(d => d.avgDelay));
                const intensity = (item.avgDelay / maxDelay) * 100;
                const bgColor = intensity > 75 ? 'bg-red-500' :
                               intensity > 50 ? 'bg-orange-500' :
                               intensity > 25 ? 'bg-yellow-500' : 'bg-green-500';

                return (
                  <div key={item.day} className="flex items-center space-x-4">
                    <div className="w-24 text-sm font-medium text-gray-700">{item.day}</div>
                    <div className="flex-1 bg-gray-100 rounded-full h-8 relative overflow-hidden">
                      <div
                        className={`${bgColor} h-full rounded-full transition-all duration-500 flex items-center justify-end pr-3`}
                        style={{ width: `${intensity}%` }}
                      >
                        <span className="text-xs font-semibold text-white">{item.avgDelay} min</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Incident Details Table */}
        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Incident Types</h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Incident Type</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Count</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Percentage</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Frequency</th>
                </tr>
              </thead>
              <tbody>
                {data.incidentBreakdown.map((incident, index) => (
                  <tr key={index} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                    <td className="py-3 px-4 text-sm text-gray-900">{incident.type}</td>
                    <td className="py-3 px-4 text-sm text-gray-600">{incident.count.toLocaleString()}</td>
                    <td className="py-3 px-4 text-sm text-gray-600">{incident.percentage}%</td>
                    <td className="py-3 px-4">
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                          style={{ width: `${incident.percentage}%` }}
                        ></div>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

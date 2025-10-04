import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';

export default function DelayChart({ data }) {
  return (
    <div className="w-full h-72">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="delayGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#0066FF" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#0066FF" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
          <XAxis
            dataKey="time"
            stroke="#6b7280"
            style={{ fontSize: '11px', fontWeight: 500 }}
            tickLine={false}
            axisLine={{ stroke: '#e5e7eb' }}
          />
          <YAxis
            stroke="#6b7280"
            style={{ fontSize: '11px', fontWeight: 500 }}
            tickLine={false}
            axisLine={{ stroke: '#e5e7eb' }}
            label={{
              value: 'Minutes',
              angle: -90,
              position: 'insideLeft',
              style: { fontSize: '11px', fill: '#6b7280', fontWeight: 600 }
            }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(255, 255, 255, 0.98)',
              border: '1px solid #e5e7eb',
              borderRadius: '12px',
              boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
              padding: '12px',
              fontFamily: 'Inter, sans-serif'
            }}
            labelStyle={{
              fontWeight: 600,
              color: '#111827',
              marginBottom: '4px'
            }}
            itemStyle={{
              color: '#0066FF',
              fontWeight: 500
            }}
            formatter={(value) => [`${value} min`, 'Delay']}
          />
          <Area
            type="monotone"
            dataKey="delay"
            stroke="#0066FF"
            strokeWidth={3}
            fill="url(#delayGradient)"
            dot={{ fill: '#0066FF', r: 5, strokeWidth: 2, stroke: '#fff' }}
            activeDot={{ r: 7, strokeWidth: 2, stroke: '#fff' }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

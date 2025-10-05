import { useState, useEffect } from 'react';
import { format } from 'date-fns';

export default function TimeSlider({ currentTime, timeRange, onChange }) {
  const [sliderValue, setSliderValue] = useState(0);
  const [dateTimeInput, setDateTimeInput] = useState('');

  useEffect(() => {
    if (timeRange && currentTime) {
      const start = new Date(timeRange.start).getTime();
      const end = new Date(timeRange.end).getTime();
      const current = new Date(currentTime).getTime();
      const percentage = ((current - start) / (end - start)) * 100;
      setSliderValue(percentage);

      // Update input field with current time
      setDateTimeInput(format(currentTime, "yyyy-MM-dd'T'HH:mm"));
    }
  }, [currentTime, timeRange]);

  const handleSliderChange = (e) => {
    const percentage = parseFloat(e.target.value);
    setSliderValue(percentage);

    const start = new Date(timeRange.start).getTime();
    const end = new Date(timeRange.end).getTime();
    const timestamp = start + (percentage / 100) * (end - start);

    onChange(new Date(timestamp));
  };

  const handleDateTimeChange = (e) => {
    const value = e.target.value;
    setDateTimeInput(value);

    try {
      const selectedDate = new Date(value);
      const start = new Date(timeRange.start).getTime();
      const end = new Date(timeRange.end).getTime();
      const selected = selectedDate.getTime();

      // Check if within range
      if (selected >= start && selected <= end) {
        onChange(selectedDate);
      }
    } catch (error) {
      console.error('Invalid date format:', error);
    }
  };

  return (
    <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 bg-white rounded-2xl shadow-soft-lg px-8 py-4 w-[600px] animate-fade-in">
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">Time Period</span>
          <span className="text-sm font-semibold text-accent">
            {currentTime && format(currentTime, 'MMM d, yyyy HH:mm')}
          </span>
        </div>

        {/* Date/Time Input */}
        <div className="flex items-center space-x-3">
          <label className="text-xs font-medium text-gray-600">Jump to:</label>
          <input
            type="datetime-local"
            value={dateTimeInput}
            onChange={handleDateTimeChange}
            min={timeRange && format(new Date(timeRange.start), "yyyy-MM-dd'T'HH:mm")}
            max={timeRange && format(new Date(timeRange.end), "yyyy-MM-dd'T'HH:mm")}
            className="flex-1 px-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <input
          type="range"
          min="0"
          max="100"
          step="0.1"
          value={sliderValue}
          onChange={handleSliderChange}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-accent"
        />

        <div className="flex justify-between text-xs text-gray-500">
          <span>{timeRange && format(new Date(timeRange.start), 'MMM yyyy')}</span>
          <span>{timeRange && format(new Date(timeRange.end), 'MMM yyyy')}</span>
        </div>
      </div>
    </div>
  );
}

interface Props {
  value: number;
}

export default function UptimeBar({ value }: Props) {
  const percent = Math.min(100, Math.max(0, value));

  return (
    <div>
      <div className="text-sm text-gray-600 mb-1">
        {percent.toFixed(1)}% uptime (24г)
      </div>

      <div className="w-full bg-gray-100 rounded-full h-2">
        <div
          className="bg-blue-500 h-2 rounded-full transition-all duration-500"
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}

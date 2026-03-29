interface Props {
  status: "UP" | "DOWN" | null;
}

export default function StatusBadge({ status }: Props) {
  if (!status) {
    return (
      <span className="px-3 py-1 text-xs rounded-full bg-yellow-100 text-yellow-700">
        Невідомо
      </span>
    );
  }

  if (status === "UP") {
    return (
      <span className="px-3 py-1 text-xs rounded-full bg-green-100 text-green-700">
        UP
      </span>
    );
  }

  return (
    <span className="px-3 py-1 text-xs rounded-full bg-red-100 text-red-700">
      DOWN
    </span>
  );
}

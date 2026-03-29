export default function Header() {
  return (
    <header className="bg-white border-b border-gray-200 px-8 py-4 flex justify-between items-center">
      <h1 className="text-xl font-bold text-blue-600">WebCheck</h1>

      <button
        onClick={() => {
          localStorage.clear();
          window.location.href = "/login";
        }}
        className="text-sm text-gray-500 hover:text-black transition"
      >
        Вихід із системи
      </button>
    </header>
  );
}

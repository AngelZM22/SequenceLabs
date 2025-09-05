import SearchPage from "./pages/SearchPage";

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-4 py-3 font-semibold">
          TFG Fútbol — Frontend
        </div>
      </header>
      <main className="max-w-6xl mx-auto p-4">
        <SearchPage />
      </main>
    </div>
  );
}

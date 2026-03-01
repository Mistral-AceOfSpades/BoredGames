import { Outlet } from 'react-router-dom';
import { Navbar } from './Navbar';

export function Layout() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
      <footer className="border-t border-game-border py-4 text-center text-sm text-gray-500">
        <p>BoredGames — AI Board Game Moderator powered by Mistral AI</p>
      </footer>
    </div>
  );
}

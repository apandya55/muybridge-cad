import Studio from "@/components/Studio";

export default function Home() {
  return (
    <main className="min-h-screen px-4 py-5 md:px-6 lg:px-8">
      <header className="mb-5 flex items-baseline gap-3">
        <span className="font-mono text-xs text-lo">
          muybridge / cad
        </span>
        <h1 className="text-base font-medium text-hi">
          Part verification
        </h1>
      </header>
      <Studio />
    </main>
  );
}

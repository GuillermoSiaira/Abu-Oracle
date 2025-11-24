import BirthDataPanel from "@/components/birth-data-panel";

export default function Home() {
  return (
    <main className="min-h-screen bg-background">
      <div className="container mx-auto py-12 space-y-12">
        <header className="text-center space-y-2">
          <h1 className="text-5xl font-serif tracking-tight text-primary">
            Abu — Astrología Persa
          </h1>
          <p className="text-muted-foreground max-w-xl mx-auto">
            Sabiduría celeste interpretada por Abu y Lilly, tradición persa aplicada al presente.
          </p>
        </header>

        <div className="max-w-2xl mx-auto">
          <BirthDataPanel />
        </div>
      </div>
    </main>
  );
}

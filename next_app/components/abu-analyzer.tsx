"use client";

import { useState } from "react";
import { Button } from "@/components/ui/simple-button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/simple-card";
import { Input } from "@/components/ui/simple-input";
import { Label } from "@/components/ui/simple-label";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/simple-tabs";
import {
  Loader2,
  Moon,
  Star,
  Sun,
  AlertCircle,
} from "lucide-react";
import { ResultsDisplay } from "@/components/results-display";

interface BirthData {
  name: string;
  date: string;
  time: string;
  city: string;
  country: string;
  lat: string;
  lon: string;
}

interface CurrentData {
  lat: string;
  lon: string;
}

export function AbuAnalyzer() {
  const [birthData, setBirthData] = useState<BirthData>({
    name: "",
    date: "1990-07-05",
    time: "12:00",
    city: "",
    country: "",
    lat: "-34.6",
    lon: "-58.4",
  });

  const [currentData, setCurrentData] = useState<CurrentData>({
    lat: "-34.6",
    lon: "-58.4",
  });

  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [wheelOrientation, setWheelOrientation] = useState<
    "aries" | "ascendant"
  >("aries");

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);

    try {
      const birthDateTime = `${birthData.date}T${birthData.time}:00Z`;

      const params = new URLSearchParams({
        date: birthDateTime,
        lat: birthData.lat,
        lon: birthData.lon,
      });

      const backendUrl =
        process.env.NEXT_PUBLIC_ABU_API_URL || "http://localhost:8000";

      console.log(
        "[v0] Calling GET /api/astro/chart/extended with params:",
        params.toString()
      );

      const response = await fetch(
        `${backendUrl}/api/astro/chart/extended?${params.toString()}`,
        {
          method: "GET",
          headers: {
            Accept: "application/json",
          },
        }
      );

      if (response.status === 502) {
        setError(
          "Error en Abu Engine. El servicio de astrología no está disponible en este momento."
        );
        return;
      }

      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      console.log(
        "[v0] Received data from /api/astro/chart/extended:",
        data
      );

      const enrichedData = {
        ...data,
        person: {
          name: birthData.name || null,
          birth_city: birthData.city || null,
          birth_country: birthData.country || null,
        },
        birth: {
          date: birthDateTime,
          lat: parseFloat(birthData.lat),
          lon: parseFloat(birthData.lon),
        },
        current: {
          lat: parseFloat(currentData.lat),
          lon: parseFloat(currentData.lon),
        },
      };

      setResults(enrichedData);
    } catch (err) {
      console.error("[v0] Error calling /api/astro/chart/extended:", err);
      setError(
        err instanceof Error
          ? err.message
          : "Error desconocido al conectar con el backend"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-12 max-w-7xl">
      <header className="text-center mb-16 space-y-6">
        <div className="flex items-center justify-center gap-4 mb-6">
          <Star className="w-10 h-10 text-primary animate-pulse" />
          <h1 className="text-6xl md:text-7xl font-serif tracking-tight">
            Abu
          </h1>
          <Moon className="w-10 h-10 text-primary animate-pulse" />
        </div>
        <p className="text-xl md:text-2xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
          Interpretación celeste según la tradición de los sabios de Persia
        </p>
      </header>

      <Card className="mb-12 border-2 border-primary/30 shadow-2xl">
        <CardHeader className="space-y-3">
          <CardTitle className="flex items-center gap-3 text-2xl font-serif">
            <Sun className="w-6 h-6 text-primary" />
            Datos de Nacimiento y Ubicación
          </CardTitle>
          <CardDescription className="text-base leading-relaxed">
            Ingresa tu información natal y ubicación actual para revelar tu
            configuración celeste
          </CardDescription>
        </CardHeader>

        <CardContent>
          <Tabs defaultValue="birth" className="w-full">
            <TabsList className="grid w-full grid-cols-2 mb-6">
              <TabsTrigger value="birth">Nacimiento</TabsTrigger>
              <TabsTrigger value="current">Ubicación Actual</TabsTrigger>
            </TabsList>

            {/* ================== BIRTH DATA ================== */}
            <TabsContent value="birth" className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="birth-name">Nombre Completo</Label>
                <Input
                  id="birth-name"
                  type="text"
                  placeholder="Tu nombre"
                  value={birthData.name}
                  onChange={(e) =>
                    setBirthData({ ...birthData, name: e.target.value })
                  }
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="birth-date">Fecha</Label>
                  <Input
                    id="birth-date"
                    type="date"
                    value={birthData.date}
                    onChange={(e) =>
                      setBirthData({ ...birthData, date: e.target.value })
                    }
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="birth-time">Hora (UTC)</Label>
                  <Input
                    id="birth-time"
                    type="time"
                    value={birthData.time}
                    onChange={(e) =>
                      setBirthData({ ...birthData, time: e.target.value })
                    }
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="birth-city">Ciudad</Label>
                  <Input
                    id="birth-city"
                    type="text"
                    placeholder="Buenos Aires"
                    value={birthData.city}
                    onChange={(e) =>
                      setBirthData({ ...birthData, city: e.target.value })
                    }
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="birth-country">País</Label>
                  <Input
                    id="birth-country"
                    type="text"
                    placeholder="Argentina"
                    value={birthData.country}
                    onChange={(e) =>
                      setBirthData({ ...birthData, country: e.target.value })
                    }
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="birth-lat">Latitud</Label>
                  <Input
                    id="birth-lat"
                    type="number"
                    step="0.1"
                    placeholder="-34.6"
                    value={birthData.lat}
                    onChange={(e) =>
                      setBirthData({ ...birthData, lat: e.target.value })
                    }
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="birth-lon">Longitud</Label>
                  <Input
                    id="birth-lon"
                    type="number"
                    step="0.1"
                    placeholder="-58.4"
                    value={birthData.lon}
                    onChange={(e) =>
                      setBirthData({ ...birthData, lon: e.target.value })
                    }
                  />
                </div>
              </div>
            </TabsContent>

            {/* ================== CURRENT LOCATION ================== */}
            <TabsContent value="current" className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="current-lat">Latitud Actual</Label>
                  <Input
                    id="current-lat"
                    type="number"
                    step="0.1"
                    placeholder="-34.6"
                    value={currentData.lat}
                    onChange={(e) =>
                      setCurrentData({ ...currentData, lat: e.target.value })
                    }
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="current-lon">Longitud Actual</Label>
                  <Input
                    id="current-lon"
                    type="number"
                    step="0.1"
                    placeholder="-58.4"
                    value={currentData.lon}
                    onChange={(e) =>
                      setCurrentData({ ...currentData, lon: e.target.value })
                    }
                  />
                </div>
              </div>
            </TabsContent>
          </Tabs>

          {/* =============== ORIENTACIÓN RUEDA =============== */}
          <div className="mt-8 p-4 rounded-lg border-2 border-primary/30 bg-card/30">
            <Label className="text-base font-semibold mb-3 block">
              Orientación de la Rueda
            </Label>

            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setWheelOrientation("aries")}
                className={`p-4 rounded-lg border-2 transition-all ${
                  wheelOrientation === "aries"
                    ? "border-primary bg-primary/10 shadow-lg"
                    : "border-border hover:border-primary/50"
                }`}
              >
                <div className="text-center space-y-2">
                  <div className="text-2xl">♈</div>
                  <div className="font-semibold">Aries arriba</div>
                  <div className="text-xs text-muted-foreground">
                    Orden tradicional del zodiaco
                  </div>
                </div>
              </button>

              <button
                type="button"
                onClick={() => setWheelOrientation("ascendant")}
                className={`p-4 rounded-lg border-2 transition-all ${
                  wheelOrientation === "ascendant"
                    ? "border-primary bg-primary/10 shadow-lg"
                    : "border-border hover:border-primary/50"
                }`}
              >
                <div className="text-center space-y-2">
                  <div className="text-2xl">AC</div>
                  <div className="font-semibold">Ascendente arriba</div>
                  <div className="text-xs text-muted-foreground">
                    Perspectiva personal del nativo
                  </div>
                </div>
              </button>
            </div>
          </div>

          {/* =============== ANALYZE BUTTON =============== */}
          <Button
            onClick={handleAnalyze}
            disabled={loading}
            className="w-full mt-8 h-14 text-lg font-semibold bg-primary hover:bg-primary/90 transition-all duration-300"
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                Consultando las estrellas...
              </>
            ) : (
              <>
                <Star className="mr-2 h-5 w-5" />
                Calcular Configuración Celeste
              </>
            )}
          </Button>

          {/* =============== ERROR MESSAGE =============== */}
          {error && (
            <div className="mt-6 p-5 bg-destructive/10 border-2 border-destructive/30 rounded-lg backdrop-blur">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-destructive mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-destructive font-medium">{error}</p>
                  {error.includes("Abu Engine") && (
                    <p className="text-sm text-muted-foreground mt-2">
                      Por favor, verifica que el servicio de backend esté
                      funcionando correctamente.
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* =============== RESULTS =============== */}
      {results && (
        <ResultsDisplay
          results={results}
          birthData={birthData}
          wheelOrientation={wheelOrientation}
        />
      )}
    </div>
  );
}

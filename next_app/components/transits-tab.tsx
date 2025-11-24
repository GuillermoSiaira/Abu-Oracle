// next_app/components/transits-tab.tsx
"use client";

import { useAppStore } from "@/lib/store";

// 👉 nuevos componentes simples
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/simple-card";

import { Badge } from "@/components/ui/simple-badge";

import { Moon, Sparkles } from "lucide-react";

export function TransitsTab() {
  const abuData = useAppStore((s) => s.abuData);
  const lunar = abuData?.derived?.lunar_transit;

  if (!lunar || lunar.moon_position == null) {
    return (
      <div className="p-6 text-center text-sm text-muted-foreground">
        No hay datos de tránsitos disponibles en este momento.
      </div>
    );
  }

  const sortedAspects = [...lunar.aspects].sort(
    (a, b) => Math.abs(a.orb) - Math.abs(b.orb)
  );

  type Strength = "fuerte" | "moderado" | "suave";

  function getStrength(orb: number): Strength {
    const abs = Math.abs(orb);
    if (abs <= 1) return "fuerte";
    if (abs <= 3) return "moderado";
    return "suave";
  }

  function strengthBadge(strength: Strength) {
    switch (strength) {
      case "fuerte":
        return (
          <Badge className="text-xs uppercase tracking-wide">
            Fuerte
          </Badge>
        );
      case "moderado":
        return (
          <Badge variant="outline" className="text-xs uppercase tracking-wide">
            Moderado
          </Badge>
        );
      case "suave":
        return (
          <Badge
            variant="outline"
            className="text-xs uppercase tracking-wide opacity-70"
          >
            Suave
          </Badge>
        );
    }
  }

  return (
    <div className="space-y-6">
      {/* POSICIÓN LUNAR */}
      <Card className="border border-border/60 bg-card/70 backdrop-blur-sm">
        <CardHeader className="flex flex-row items-center gap-2 pb-2">
          <Moon className="h-5 w-5 opacity-80" />
          <CardTitle className="text-base font-semibold">
            Posición lunar actual
          </CardTitle>
        </CardHeader>

        <CardContent className="pt-0">
          <p className="text-2xl font-semibold">
            {lunar.moon_position.toFixed(2)}°
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            Longitud eclíptica de la Luna para este momento.
          </p>
        </CardContent>
      </Card>

      {/* ASPECTOS LUNARES */}
      <Card className="border border-border/60 bg-card/70 backdrop-blur-sm">
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 opacity-80" />
            <CardTitle className="text-base font-semibold">
              Aspectos lunares al mapa natal
            </CardTitle>
          </div>

          <span className="text-xs text-muted-foreground">
            {sortedAspects.length} aspecto
            {sortedAspects.length === 1 ? "" : "s"}
          </span>
        </CardHeader>

        <CardContent className="pt-0">
          {sortedAspects.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              Sin aspectos lunares relevantes en este momento.
            </p>
          ) : (
            <div className="space-y-2">
              {sortedAspects.map((asp: any, i: number) => {
                const strength = getStrength(asp.orb);

                return (
                  <div
                    key={i}
                    className="flex items-start justify-between rounded-lg border bg-background/60 px-3 py-2 text-sm"
                  >
                    <div className="space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-medium">{asp.type}</span>
                        <span className="text-xs text-muted-foreground">
                          con
                        </span>
                        <span className="font-semibold">{asp.planet}</span>
                      </div>

                      <div className="text-xs text-muted-foreground">
                        Orbe: {asp.orb.toFixed(2)}°
                      </div>
                    </div>

                    <div className="ml-3 shrink-0">
                      {strengthBadge(strength)}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
  
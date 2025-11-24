"use client";

import { useState, useEffect, useRef } from "react";

interface CityResult {
  city: string;
  country: string;
  lat: number;
  lon: number;
}

interface CityAutocompleteProps {
  onSelect: (data: { city: string; lat: number; lon: number }) => void;
}

export default function CityAutocomplete({ onSelect }: CityAutocompleteProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<CityResult[]>([]);
  const [showList, setShowList] = useState(false);
  const debounceRef = useRef<NodeJS.Timeout | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setShowList(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Debounced city search
  useEffect(() => {
    if (query.length < 2) {
      setResults([]);
      return;
    }

    if (debounceRef.current) clearTimeout(debounceRef.current);

    debounceRef.current = setTimeout(async () => {
      try {
        const base =
          process.env.NEXT_PUBLIC_ABU_URL || "http://localhost:8000";

        const res = await fetch(
          `${base}/api/cities/search?q=${encodeURIComponent(query)}`
        );

        if (res.ok) {
          const data = await res.json();
          setResults(data);
          setShowList(true);
        }
      } catch (err) {
        console.error("Autocomplete error:", err);
      }
    }, 300); // 300ms debounce delay
  }, [query]);

  // Handle city selection
  function handleSelect(c: CityResult) {
    setQuery(`${c.city}, ${c.country}`);
    setShowList(false);

    onSelect({
      city: `${c.city}, ${c.country}`,
      lat: c.lat,
      lon: c.lon,
    });
  }

  return (
    <div ref={containerRef} className="relative space-y-1">
      <label className="block text-sm font-medium">Ciudad</label>

      <input
        type="text"
        placeholder="Ingresa una ciudad"
        className="w-full rounded-md border px-3 py-2"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => {
          if (results.length > 0) setShowList(true);
        }}
      />

      {showList && results.length > 0 && (
        <ul className="absolute w-full bg-white border rounded-md shadow-lg z-30 max-h-48 overflow-y-auto">
          {results.map((c, i) => (
            <li
              key={i}
              className="px-3 py-2 cursor-pointer hover:bg-gray-100"
              onClick={() => handleSelect(c)}
            >
              {c.city}, {c.country}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

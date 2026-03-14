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
  label?: string;
  placeholder?: string;
}

export default function CityAutocomplete({ onSelect, label = "Ciudad", placeholder = "Ingresa una ciudad" }: CityAutocompleteProps) {
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
        const res = await fetch(
          `/api/cities/search?q=${encodeURIComponent(query)}`
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
      <label className="block text-sm font-semibold text-gray-700">{label}</label>

      <input
        type="text"
        placeholder={placeholder}
        className="w-full bg-white text-gray-950 border border-gray-300 rounded-md px-3 py-2 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => {
          if (results.length > 0) setShowList(true);
        }}
      />

      {showList && results.length > 0 && (
        <ul className="absolute w-full bg-white border border-gray-200 rounded-md shadow-xl z-50 max-h-48 overflow-y-auto mt-1">
          {results.map((c, i) => (
            <li
              key={i}
              className="px-3 py-2 cursor-pointer text-gray-900 hover:bg-amber-50 transition-colors"
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
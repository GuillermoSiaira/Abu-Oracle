# Component Map: next_app/components & next_app/app

---

## next_app/components

### zodiac-wheel.tsx
- **Imports:** useMemo (react)
- **Exports:** None detected in first 40 lines (likely default or named later)
- **Component(s):** None detected in first 40 lines
- **Notes:** No missing imports detected

### transits-tab.tsx
- **Imports:** Card, CardContent, CardHeader, CardTitle (@/components/ui/card); useAppStore (@/lib/store)
- **Exports:** `TransitsTab` (named)
- **Component(s):** TransitsTab
- **Notes:** No missing imports detected

### theme-provider.tsx
- **Imports:** NextThemesProvider, ThemeProviderProps (next-themes)
- **Exports:** `ThemeProvider` (named)
- **Component(s):** ThemeProvider
- **Notes:** No missing imports detected

### results-display.tsx
- **Imports:** useState (react); Card, CardContent, CardDescription, CardHeader, CardTitle (@/components/ui/card); Tabs, TabsContent, TabsList, TabsTrigger (@/components/ui/tabs); Badge (@/components/ui/badge); Button (@/components/ui/button); Moon, Star, Sun, Sparkles, Activity, Calendar, Loader2, MessageSquare (lucide-react); ZodiacWheel (@/components/zodiac-wheel)
- **Exports:** None detected in first 40 lines (likely default or named later)
- **Component(s):** None detected in first 40 lines
- **Notes:** No missing imports detected

### profections-view.tsx
- **Imports:** Card, CardContent, CardHeader, CardTitle (@/components/ui/card)
- **Exports:** `ProfectionsView` (named)
- **Component(s):** ProfectionsView
- **Notes:** No missing imports detected

### positions-table.tsx
- **Imports:** Card, CardContent, CardHeader, CardTitle (@/components/ui/card); Table, TableBody, TableCell, TableHead, TableHeader, TableRow (@/components/ui/table); Badge (@/components/ui/badge)
- **Exports:** None detected in first 40 lines (likely default or named later)
- **Component(s):** None detected in first 40 lines
- **Notes:** No missing imports detected

### planets-table.tsx
- **Imports:** Planet (@/lib/types); Badge (@/components/ui/badge)
- **Exports:** `PlanetsTable` (named)
- **Component(s):** PlanetsTable
- **Notes:** No missing imports detected

### persian-techniques-tab.tsx
- **Imports:** useAppStore (@/lib/store)
- **Exports:** `PersianTechniquesTab` (named)
- **Component(s):** PersianTechniquesTab
- **Notes:** No missing imports detected

### natal-chart-tab.tsx
- **Imports:** useAppStore (@/lib/store)
- **Exports:** `NatalChartTab` (named)
- **Component(s):** NatalChartTab
- **Notes:** No missing imports detected

---

## next_app/app

### page.tsx
- **Imports:** BirthDataPanel (@/components/birth-data-panel)
- **Exports:** `Home` (default)
- **Component(s):** Home
- **Notes:** No missing imports detected

### layout.tsx
- **Imports:** Metadata (next); DM_Serif_Display, Inter (next/font/google); ./globals.css
- **Exports:** `metadata` (named), `RootLayout` (default)
- **Component(s):** RootLayout
- **Notes:** No missing imports detected

### chart/page.tsx
- **Imports:** useAppStore (@/lib/store); ChartTabs (@/components/chart-tabs); ChatPanel (@/components/chat-panel)
- **Exports:** `ChartPage` (default)
- **Component(s):** ChartPage
- **Notes:** No missing imports detected

---

## Export Consistency & Issues
- No missing imports detected in scanned files.
- All exports appear consistent (default exports imported as default, named as named).
- No inconsistencies (default exported but imported as named, or vice versa) detected in scanned files.

---

*This report is based on the first 40 lines of each file. For files with more complex export logic, a deeper scan may be needed.*

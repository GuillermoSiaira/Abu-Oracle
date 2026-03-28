/**
 * Shared astrological utilities — traditional Hellenistic rulerships.
 * Used by relocation-tab, natal-chart-tab (click_house), and any future consumers.
 */

export const SIGN_LORDS: Record<string, string> = {
  Aries:       'Mars',
  Taurus:      'Venus',
  Gemini:      'Mercury',
  Cancer:      'Moon',
  Leo:         'Sun',
  Virgo:       'Mercury',
  Libra:       'Venus',
  Scorpio:     'Mars',
  Sagittarius: 'Jupiter',
  Capricorn:   'Saturn',
  Aquarius:    'Saturn',
  Pisces:      'Jupiter',
};

const SIGNS = [
  'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
];

/** Returns the traditional lord of a sign (empty string if unknown). */
export function getHouseLord(cuspSign: string): string {
  return SIGN_LORDS[cuspSign] ?? '';
}

/**
 * Returns the significators of a house: [lord, ...occupants].
 * houseCusps entries use `start` as the cusp longitude in degrees.
 */
export function deriveSignificators(
  houseNum: number,
  planets: Array<{ name: string; house: number; sign?: string }>,
  houseCusps: Array<{ house: number; start: number }>
): string[] {
  const cusp = houseCusps.find(h => h.house === houseNum);
  const cuspSign = cusp ? SIGNS[Math.floor(cusp.start / 30) % 12] : null;
  const lord = cuspSign ? SIGN_LORDS[cuspSign] : null;
  const occupants = planets.filter(p => p.house === houseNum).map(p => p.name);
  return lord ? [lord, ...occupants.filter(p => p !== lord)] : occupants;
}

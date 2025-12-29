import { ChevronRight } from "lucide-react";

type OracleContent = {
	headline?: string;
	narrative?: string;
	actions?: string[];
	astro_metadata?: {
		source?: string;
		[key: string]: any;
	};
};

interface OracleResponseProps {
	content: string;
}

// Export default function directa para evitar errores de importación
export default function OracleResponse({ content }: OracleResponseProps) {
	let parsed: OracleContent | null = null;

	try {
		const cleanContent = content.replace(/```json/g, "").replace(/```/g, "").trim();
		parsed = JSON.parse(cleanContent);
	} catch {
		parsed = null;
	}

	// Fallback: Texto plano
	if (!parsed) {
		return (
			<div className="text-purple-100 whitespace-pre-wrap leading-relaxed">
				{content}
			</div>
		);
	}

	// Renderizado Rico
	return (
		<div className="bg-purple-900/40 p-5 rounded-lg border border-purple-700/50 shadow-sm mt-2">
			{parsed.headline && (
				<h3 className="text-yellow-400 font-serif text-xl mb-3 border-b border-yellow-400/20 pb-2">
					{parsed.headline}
				</h3>
			)}
      
			{parsed.narrative && (
				<p className="text-purple-50 leading-relaxed mb-4 text-[15px]">
					{parsed.narrative}
				</p>
			)}

			{parsed.actions && parsed.actions.length > 0 && (
				<div className="bg-purple-950/50 rounded-lg p-3 border border-purple-800/30">
					<p className="text-[11px] text-purple-400 uppercase tracking-widest mb-2 font-bold">
						Recomendaciones
					</p>
					<ul className="space-y-2">
						{parsed.actions.map((action, idx) => (
							<li key={idx} className="flex items-start gap-2 text-sm text-yellow-100/90">
								<ChevronRight size={16} className="text-yellow-500 mt-0.5 shrink-0" />
								<span>{action}</span>
							</li>
						))}
					</ul>
				</div>
			)}

			<div className="mt-3 flex justify-end">
				<span className="text-[10px] text-purple-400/60 font-mono bg-purple-950/30 px-2 py-1 rounded">
					{parsed.astro_metadata?.source || "AI Oracle"}
				</span>
			</div>
		</div>
	);
}



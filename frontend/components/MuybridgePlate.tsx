"use client";
import Image from "next/image";
import { ExternalLink } from "lucide-react";

export default function MuybridgePlate({
  plateUrl,
  running,
}: {
  plateUrl: string | null;
  running: boolean;
}) {
  return (
    <div className="relative h-full w-full flex flex-col justify-center">
      {plateUrl ? (
        <div className="relative h-full w-full min-h-[220px]">
          <Image
            src={plateUrl}
            alt="12-angle Muybridge contact sheet"
            fill
            sizes="(min-width: 1024px) 40vw, 100vw"
            unoptimized
            className="object-contain rounded-md"
          />
          <a
            href={plateUrl}
            target="_blank"
            rel="noopener noreferrer"
            title="Open high-res plate"
            className="absolute right-2 top-2 inline-flex items-center gap-1 rounded-md bg-overlay/80 px-2 py-1 text-2xs text-mid hover:text-hi border border-hi backdrop-blur transition-colors"
          >
            <span>Full resolution</span>
            <ExternalLink className="h-2.5 w-2.5" />
          </a>
        </div>
      ) : (
        <div className="flex h-full min-h-[180px] items-center justify-center rounded-lg bg-overlay/30 border border-hi">
          <div className="text-center">
            <div className="font-mono text-xs text-lo">
              Muybridge plate
            </div>
            <div className="mt-1 text-2xs text-lo">
              {running ? "Rendering 12 views…" : "Run a part to see the inspection views."}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

"use client";

import type { StruggleOffer } from "@/lib/types";

interface StruggleOfferBannerProps {
  offers: StruggleOffer[];
  onRespond: (offerId: string, accepted: boolean) => void;
}

export function StruggleOfferBanner({ offers, onRespond }: StruggleOfferBannerProps) {
  if (offers.length === 0) return null;

  return (
    <>
      {offers.map((offer) => (
        <div className="struggle" key={offer.offer_id}>
          <div className="kicker">Struggle-Detector offer</div>
          <p>{offer.reason}</p>
          <div className="struggle-actions">
            <button className="yes" onClick={() => onRespond(offer.offer_id, true)}>
              Yes, drill it
            </button>
            <button className="no" onClick={() => onRespond(offer.offer_id, false)}>
              Not actually stuck
            </button>
          </div>
        </div>
      ))}
    </>
  );
}

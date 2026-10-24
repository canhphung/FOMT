# English sources

`pilot.json` and `items.json` preserve the verified English records corresponding
to the Vietnamese draft files. They are subsets, not the whole game. `shop_items.json` preserves the 26 verified native shop/item-window literals added in items-complete.

Run `python3 tools/text_extractor.py /path/to/base.gba` from the repository root
to regenerate `catalog.json`: 9,309 records, including every string in the
1,328 referenced SCR containers. The complete generated catalog is ignored by
Git; it exists locally after extraction. No ROM is included or downloaded.

Addresses, original bytes, pointer/offset locations and source references are
generated from the exact supported ROM, never supplied by a translator. The
inserter re-extracts these fields independently instead of trusting JSON offsets.

`npc_daily.json` preserves 85 verified standard-dialogue sources for Thomas and
Popuri, including guarded actor/ShowText provenance. Trigger coverage and
untranslated spouse/home records are tracked in `../npc_coverage.json`.

`object_labels.json` preserves the 261 verified examined-object label records.
The source-only ID/CODE/display-site contract is `../object_labels.json`.

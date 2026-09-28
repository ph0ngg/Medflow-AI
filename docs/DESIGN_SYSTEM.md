# DESIGN SYSTEM — MedFlow AI (UI tokens & components)

Nguồn: `frontend/src/styles.css` (CSS variables), `frontend/src/components/ui.tsx`.

## Tokens (CSS variables)
```css
--bg: #f4f7fb;            --surface: #ffffff;
--text: #1a2433;          --muted: #5b6b7e;
--primary: #0b6bcb;       --secondary: #e7eef7;
--danger: #d3232f;        --ok: #1c8a4e; --warn: #b26a00;
--radius: 16px;           --shadow: 0 6px 20px rgba(20,40,80,.08);
--font-size: 20px;        --font-size-lg: 26px;  --font-size-xl: 36px;
```

## Accessibility
- Font ≥ 18–20px; nút min-height 56px; tương phản cao.
- Focus visible; `aria-live` cho transcript chat.
- Responsive: dưới 600px giảm cỡ chữ, grid 1 cột.

## Components
- `BigButton` (primary/secondary/danger)
- `Card`, `QueueInfoCard`, `TicketCard`, `WayfindingCard`
- `StatusBar`, `Spinner`, `formatVnd`
- `CameraFeed` (video + capture + auto-detect)
- `VoiceButton` (push-to-talk)

## Kiosk dimensions
Thiết kế cho màn hình kiosk 1080p ngang; max-width 900px khi chạy trên desktop.

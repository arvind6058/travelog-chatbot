# TravelLogix Admin Portal (`admin/`)

Dedicated Administrative and Operations Frontend application built with Next.js 14, React, TypeScript, and Tailwind CSS.

## Key Architecture Rules
- **Port**: Runs on `http://localhost:3053`.
- **Clean Root Layout**: Dedicated operations console styling with dark mode design system.
- **Standalone Login**: `/admin/login` renders only the internal admin authentication card. No public registration or driver login forms exist.
- **Dedicated Admin Layout**: Left sidebar with operations navigation across Dashboard, Shipments, Drivers, Vehicles, Telemetry Tracking, Customer Directory, and Audit Logs.
- **Two Separate Tracking Streams**: Shipment Tracking and Fleet/Driver Telemetry are decoupled into distinct views.

## Development
```bash
npm install
npm run dev
```
Runs at `http://localhost:3053`.

## Production Build
```bash
npm run build
```

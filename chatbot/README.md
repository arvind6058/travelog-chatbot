# TravelLogix Customer Frontend (`chatbot/`)

Dedicated Customer Frontend application built with Next.js 14, React, TypeScript, and Tailwind CSS.

## Key Architecture Rules
- **Port**: Runs on `http://localhost:3052`.
- **Clean Root Layout**: `app/layout.tsx` does NOT mount any chat widgets, navigation headers, or customer sidebars.
- **Route Group `(auth)`**: `/login` and `/register` render exclusively standalone auth cards.
- **Route Group `(customer)`**: Dedicated customer portal layout with top navigation for AI Assistant, Logistics Hub, My Shipments, Flights, Hotels, Trains, and Buses.
- **Zero Admin Leaks**: No admin interfaces or driver login interfaces are exposed in this application.

## Development
```bash
npm install
npm run dev
```
Runs at `http://localhost:3052`.

## Production Build
```bash
npm run build
```

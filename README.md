# recitAR (working name)

Buenos Aires event aggregator. Links to official ticket pages; does not sell tickets.

- `docs/BRIEF.md`: product brief.
- `client/`: Expo app (iOS, Android, web) with Expo Router. Web output is `static`.

## Client

```
cd client
npm install
npx expo start      # dev server
npm test            # vitest (domain and application logic)
npm run typecheck
npx expo lint
npx expo export --platform web   # static build into client/dist
```

## Structure

Code is organised by feature, then by layer (`domain`, `application`, `infrastructure`, `ui`). Routes in `client/src/app` stay thin. Design tokens in `client/src/design/tokens.ts` mirror the Figma variables.

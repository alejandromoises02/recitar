# Welcome to your Expo app 👋

This is an [Expo](https://expo.dev) project created with [`create-expo-app`](https://www.npmjs.com/package/create-expo-app).

## Get started

1. Install dependencies

   ```bash
   npm install
   ```

2. Start the app

   ```bash
   npx expo start
   ```

In the output, you'll find options to open the app in a

- [development build](https://docs.expo.dev/develop/development-builds/introduction/)
- [Android emulator](https://docs.expo.dev/workflow/android-studio-emulator/)
- [iOS simulator](https://docs.expo.dev/workflow/ios-simulator/)
- [Expo Go](https://expo.dev/go), a limited sandbox for trying out app development with Expo

You can start developing by editing the files inside the **src/app** directory. This project uses [file-based routing](https://docs.expo.dev/router/introduction).

## API types

The app only talks to the recitAR API (`server/`), and its types for what the API sends are
generated from the API's OpenAPI schema, never written by hand:

- `src/api/openapi.json`: the schema, exported by the server (`python -m app.openapi_export` in
  `server/`).
- `src/api/schema.ts`: TypeScript types generated from it with `npm run gen:api`. Do not edit it.
- `src/features/events/infrastructure/event-from-api.ts`: maps the API's event (snake_case, times as
  text) to the app's `Event` (camelCase, `Date`). It names every field, so when the API renames or
  removes one, `npm run typecheck` fails there.

After changing the API: export the schema in `server/`, run `npm run gen:api` here, then
`npm run typecheck`. Tests fail on both sides while either file is out of date.

`openapi-typescript` declares TypeScript 5 as a peer; `overrides` in `package.json` lets it use
this project's TypeScript 6, which it works with.

### Fetching data

Data comes from the API through TanStack Query (cache, retries, paging):

- Set the API address in `client/.env.local` (not committed), then fully reload the app:
  `EXPO_PUBLIC_API_URL=http://localhost:8000`. On a phone use the computer's LAN address
  (e.g. `http://192.168.0.10:8000`); on the Android emulator, `http://10.0.2.2:8000`. Without it,
  every request fails with an `ApiConfigError` that says so. Expo inlines `EXPO_PUBLIC_*` at build
  time, so read it only as `process.env.EXPO_PUBLIC_API_URL`, and never put secrets in it.
- `src/features/events/infrastructure/events-api.ts`: the HTTP client. API errors become an
  `ApiError` with the problem's `status`, `title` and `detail`; `getEvent` gives `null` for an
  unknown id.
- `src/features/events/infrastructure/events-queries.ts`: `useEvents(filters)` (infinite list that
  follows `next_cursor`), `useEvent(id)` and `useVenues()`. Each set of filters has its own cache entry.
- `src/api/query-client.ts`: data stays fresh for 5 minutes; network failures, 408, 429 and 5xx are
  retried twice, other errors are not (asking again gives the same answer).
- `src/api/app-focus.ts`: on iOS and Android, queries refresh when the app returns to the
  foreground (the browser does this by itself on web).

## Get a fresh project

When you're ready, run:

```bash
npm run reset-project
```

This command will move the starter code to the **example** directory and create a blank **src/app** directory where you can start developing.

### Other setup steps

- To set up ESLint for linting, run `npx expo lint`, or follow our guide on ["Using ESLint and Prettier"](https://docs.expo.dev/guides/using-eslint/)
- If you'd like to set up unit testing, follow our guide on ["Unit Testing with Jest"](https://docs.expo.dev/develop/unit-testing/)
- Learn more about the TypeScript setup in this template in our guide on ["Using TypeScript"](https://docs.expo.dev/guides/typescript/)

## Learn more

To learn more about developing your project with Expo, look at the following resources:

- [Expo documentation](https://docs.expo.dev/): Learn fundamentals, or go into advanced topics with our [guides](https://docs.expo.dev/guides).
- [Learn Expo tutorial](https://docs.expo.dev/tutorial/introduction/): Follow a step-by-step tutorial where you'll create a project that runs on Android, iOS, and the web.

## Join the community

Join our community of developers creating universal apps.

- [Expo on GitHub](https://github.com/expo/expo): View our open source platform and contribute.
- [Discord community](https://chat.expo.dev): Chat with Expo users and ask questions.

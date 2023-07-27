# cms

A uesio base app that provides content management functionality

## First-time setup

To get your local environment setup, first ensure that:

1. The [ues.io CLI](https://docs.ues.io/using-the-cli) is installed (Run `uesio -h` to ensure it's available)
2. [Node 18+](https://nodejs.org/en/download) is installed
3. You are added to the "Maintainers" team of the "uesio/cms" app. Ask someone at ues.io who is a maintainer to add you to the team, then verify that you can access the app by logging in to the Studio and verifying that you can see "uesio/cms" as one of the apps.
4. Run this to get setup locally:

```
git clone git@github.com:TheCloudMasters/cms.git
cd cms
npm run init
```

-   Select "uesio/cms" as the app.

## Development

You can develop both locally and/or in the Studio.

1. Pull (Studio to local): `npm run pull`
2. Push (local --> Studio): `npm run push`

## IDE Integration

VS Code is recommended for local development of custom components. TypeScript extensions should be automatically enabled.

To add a custom component

```
uesio generate component
```

Hit enter to select the `main` component pack.

## Continuous integration

The `main` branch will automatically be built and deployed to the "dev" workspace, and a new patch bundle will be created.

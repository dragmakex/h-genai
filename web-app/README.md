# web-app

#### The web app is built with [Vue 3](https://vuejs.org/), [Vite](https://vitejs.dev/) and [Shadcn UI (Vue)](https://www.shadcn-vue.com/).
![Screenshot](src/assets/images/screenshot.png)


## Structure

- `src/`: Source code for the web app.
    - `assets/`: Static assets. `records.json` holds all the data for cities above the population of 30.000 inhabitants in France. This is used to populate the dropdown.
    - `components/ui/`: Shadcn UI components.
    - `stores/`: Pinia stores. Municipalities store with all the cities data and the user selection store with the user's selection.
    - `App.vue`: Main application component.
    - `main.js`: Entry point for the application.
- `public/`: Static assets.
- `package.json`: Project dependencies and scripts. Reference install instructions below to install locally and to build for production.

## Request

The POST request is made to our deployed [FastAPI server](https://kbba87ikh5.execute-api.us-west-2.amazonaws.com/generate-pdf) with the following body (example):

```json
{
  "siren": "123456789",
  "municipality_name": "Paris",
  "municipality_code": "75056",
  "inter_municipality_name": "Hauts-de-Seine",
  "inter_municipality_code": "92001",
  "reference_sirens": ["123456789", "987654321"]
}
```

It returns a PDF file and embeds it in the page. It can be looked at in the browser and be downloaded.

## Install instructions

Prerequisites:
- Node.js
- npm

Install the dependencies:

```sh
npm install
```

### Compil and hot-reload (for development)

```sh
npm run dev
```

### Compile and minify (for production)

```sh
npm run build
```
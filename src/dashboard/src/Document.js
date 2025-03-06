import React from 'react';
import { Provider } from 'react-redux';
import { ServerStyleSheet } from 'styled-components';
import { AfterRoot, AfterData } from '@jaredpalmer/after';
import serialize from 'serialize-javascript';
import { runtimeConfig } from './config';
import configureStore from './storeConfig';
import Header from './components/Header';
import { TITLE } from './constants';

const store = configureStore();

export default class Document extends React.Component {
  static async getInitialProps({ assets, data, renderPage }) {
    const sheet = new ServerStyleSheet();
    const page = await renderPage(App => props =>
      sheet.collectStyles(
        <Provider store={store}>
          <App {...props} />
        </Provider>,
      ),
    );
    const styleTags = sheet.getStyleElement();
    return { assets, data, ...page, styleTags };
  }

  render() {
    const { helmet, assets, data, styleTags } = this.props;
    // get attributes from React Helmet
    const htmlAttrs = helmet.htmlAttributes.toComponent();
    const bodyAttrs = helmet.bodyAttributes.toComponent();
    // Grab the initial state from our Redux store
    const finalState = store.getState();
    return (
      <html {...htmlAttrs}>
        <head>
          <meta httpEquiv="X-UA-Compatible" content="IE=edge" />
          <meta charSet="utf-8" />
          <title>{TITLE}</title>
          <meta name="viewport" content="width=device-width, initial-scale=1" />
          {helmet.title.toComponent()}
          {helmet.meta.toComponent()}
          {helmet.link.toComponent()}
          {/** here is where we put our Styled Components styleTags... */}
          {styleTags}
        </head>
        <body {...bodyAttrs}>
          <Header titleText={TITLE} />
          <AfterRoot />
          <AfterData data={data} />
          <script
            dangerouslySetInnerHTML={{ __html: `window.env = ${serialize(runtimeConfig)};` }}
          />
          <script
            dangerouslySetInnerHTML={{
              __html: `window.__PRELOADED_STATE__= ${serialize(finalState)};`,
            }}
          />
          <script type="text/javascript" src={assets.client.js} defer crossOrigin="anonymous" />
        </body>
      </html>
    );
  }
}

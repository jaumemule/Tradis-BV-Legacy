import React from 'react';
import { hydrate } from 'react-dom';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { ensureReady, After } from '@jaredpalmer/after';
import { Flex } from 'rebass';
import './client.css';
import configureStore from './storeConfig';
import routes from './routes';
import * as Middleware from './contexts/middleware-client';

const containerWidth = [1, 3 / 4];

const store = configureStore(window.__PRELOADED_STATE__);

ensureReady(routes).then(data =>
  hydrate(
    <Middleware.Provider>
      <Provider store={store}>
        <BrowserRouter>
          <Flex mx="auto" my={50} width={containerWidth}>
            <After data={data} routes={routes} />
          </Flex>
        </BrowserRouter>
      </Provider>
    </Middleware.Provider>,
    document.getElementById('root'),
  ),
);

if (module.hot) {
  module.hot.accept(
    ensureReady(routes).then(data =>
      hydrate(
        <Middleware.Provider>
          <Provider store={store}>
            <BrowserRouter>
              <Flex mx="auto" my={50} width={containerWidth}>
                <After data={data} routes={routes} />
              </Flex>
            </BrowserRouter>
          </Provider>
        </Middleware.Provider>,
        document.getElementById('root'),
      ),
    ),
  );
}

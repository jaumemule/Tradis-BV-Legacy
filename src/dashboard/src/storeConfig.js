import { init } from '@rematch/core';
import createLoadingPlugin from '@rematch/loading';
import models from './models';

const loading = createLoadingPlugin({});

function configStore(initialState) {
  return init({
    models,
    plugins: [loading],
    redux: {
      initialState,
    },
  });
}

export default configStore;

import { createSelector } from 'reselect';

const selectCoinsDomain = state => state.coins;

const makeSelectCoinsIds = createSelector(
  selectCoinsDomain,
  coins => coins.ids,
);

const makeSelectCoinsData = createSelector(
  selectCoinsDomain,
  coins => coins.data,
);

export { selectCoinsDomain, makeSelectCoinsIds, makeSelectCoinsData };

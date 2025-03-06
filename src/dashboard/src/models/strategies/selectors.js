import { createSelector } from 'reselect';

const selectStrategiesDomain = state => state.strategies;

const makeSelectStrategiesIds = createSelector(
  selectStrategiesDomain,
  strategies => strategies.ids,
);

const makeSelectStrategiesData = createSelector(
  selectStrategiesDomain,
  strategies => strategies.data,
);

export { selectStrategiesDomain, makeSelectStrategiesIds, makeSelectStrategiesData };

export default {
  setStrategies(state, payload) {
    return {
      ...state,
      ids: payload.map(({ _id }) => _id),
      data: payload.reduce((data, strategy) => {
        data[strategy._id] = strategy;
        return data;
      }, {}),
    };
  },
};

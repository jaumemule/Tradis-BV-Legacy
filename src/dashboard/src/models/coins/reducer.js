export default {
  setCoins(state, payload) {
    return {
      ...state,
      ids: payload.map(({ _id }) => _id),
      data: payload.reduce((data, coin) => {
        data[coin._id] = coin;
        return data;
      }, {}),
    };
  },
};

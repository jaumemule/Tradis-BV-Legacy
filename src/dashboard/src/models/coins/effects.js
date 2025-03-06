export default {
  async requestCoins(client) {
    try {
      const response = await client.get('/coins');
      this.setCoins(response.data);
    } catch (error) {
      console.error(error);
    }
  },
};

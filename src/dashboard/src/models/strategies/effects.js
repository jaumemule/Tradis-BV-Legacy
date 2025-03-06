export default {
  async requestStrategies(client) {
    try {
      const response = await client.get('/strategies');
      this.setStrategies(response.data);
    } catch (error) {
      console.error(error);
    }
  },
};

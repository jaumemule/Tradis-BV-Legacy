import React from 'react';
import Api from './middleware-client/Api';
import LoginForm from './middleware-client/LoginForm';

const MiddlewareClientContext = React.createContext();

const ApiInstance = new Api();

const { Consumer } = MiddlewareClientContext;

const MIDDLEWARE_ITEM_KEY = 'middleware-token';

class MiddlewareClientProvider extends React.Component {
  state = { client: this.props.client, error: null };
  getClient(token) {
    ApiInstance.apiToken = token;
    return ApiInstance;
  }
  login = async data => {
    const response = await ApiInstance.post('/login', data).catch(error => {
      console.log('Oh no', error);
      this.setState({ error });
    });
    window.localStorage.setItem(MIDDLEWARE_ITEM_KEY, response.data.token);
    this.setState({ client: this.getClient(response.data.token) });
  };

  logout = () => {
    window.localStorage.removeItem(MIDDLEWARE_ITEM_KEY);
    this.setState({ client: null });
  };

  componentDidMount() {
    const token = window.localStorage.getItem(MIDDLEWARE_ITEM_KEY);
    if (token && !this.state.client) {
      this.setState({ client: this.getClient(token) });
    }
  }

  render() {
    const { client } = this.state;
    const { children } = this.props;
    return client ? (
      <MiddlewareClientContext.Provider value={{ client, logout: this.logout }}>
        {children}
      </MiddlewareClientContext.Provider>
    ) : (
      <LoginForm onSubmit={this.login} />
    );
  }
}

export { MiddlewareClientProvider as Provider, Consumer, MiddlewareClientContext as Context };

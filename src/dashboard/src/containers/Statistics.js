import React, { Component } from 'react';
import { connect } from 'react-redux';
import { Button } from 'rebass';
import * as Middleware from '../contexts/middleware-client';
import { makeSelectStrategiesData } from '../models/strategies/selectors';
import { makeSelectCoinsData } from '../models/coins/selectors';

class Statistics extends Component {
  static contextType = Middleware.Context;
  componentDidMount() {
    const { client } = this.context;
    this.props.initializeView(client);
  }
  render() {
    const { strategies, coins } = this.props;
    const { logout } = this.context || {};
    return (
      <div>
        <Button onClick={logout}>Logout</Button>
        <h2>Strategies</h2>
        <div>{strategies && <pre>{JSON.stringify(strategies, null, 2)}</pre>}</div>
        <h2>Coins</h2>
        <div>{coins && <pre>{JSON.stringify(coins, null, 2)}</pre>}</div>
      </div>
    );
  }
}

const mapStateToProps = store => ({
  strategies: makeSelectStrategiesData(store),
  coins: makeSelectCoinsData(store),
});

const mapDispatchToProps = dispatch => ({
  initializeView: client => {
    dispatch.strategies.requestStrategies(client);
    dispatch.coins.requestCoins(client);
  },
});

export default connect(
  mapStateToProps,
  mapDispatchToProps,
)(Statistics);

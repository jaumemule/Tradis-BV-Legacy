import React, { Component } from 'react';
import logo from '../react.svg';
import './Home.css';
import { Link } from 'react-router-dom';
import * as MiddlewareContext from '../contexts/middleware-client';

class Home extends Component {
  static async getInitialProps({ req, res, match, history, location, ...ctx }) {
    return { whatever: 'stuff' };
  }

  static contextType = MiddlewareContext;

  render() {
    return (
      <div className="Home">
        <div className="Home-header">
          <img src={logo} className="Home-logo" alt="logo" />
          <h2>Hi!</h2>
          <Link to="/statistics">Statistics -></Link>
        </div>
      </div>
    );
  }
}

export default Home;

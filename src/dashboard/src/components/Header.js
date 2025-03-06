import React from 'react';
import PropTypes from 'prop-types';
import styled from 'styled-components';

const Title = styled.h1`
  font-size: 16px;
  margin: 0;
`;

const TitleHeader = styled.header`
  height: 60px;
  background-color: #eaf4f4;
  padding: 8px;
`;

const Header = ({ titleText }) => (
  <TitleHeader>
    <Title>{titleText}</Title>
  </TitleHeader>
);

Header.propTypes = {
  titleText: PropTypes.string,
};

export default Header;

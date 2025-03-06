import React from 'react';
import styled from 'styled-components';
import { Flex, Button } from 'rebass';
import { Form, Field } from 'react-final-form';

const Input = styled.input`
  display: block;
  width: 100%;
  height: 34px;
  padding: 6px 12px;
  margin: 10px 0px;
  font-size: 14px;
  line-height: 1.42857143;
  color: #555;
  background-color: #fff;
  background-image: none;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-shadow: inset 0 1px 1px rgba(0, 0, 0, 0.075);
  transition: border-color ease-in-out 0.15s, box-shadow ease-in-out 0.15s;
`;

const LoginBox = styled.div`
  width: 600px;
  max-height: 300px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
`;

const TextFieldAdapter = ({ input, meta, ...rest }) => <Input {...input} {...rest} />;

const LoginForm = ({ onSubmit }) => (
  <div>
    <div>
      <Flex mx="auto" my={50} width={[1, 3 / 4]} alignItems="center">
        <Form
          onSubmit={onSubmit}
          render={({ handleSubmit, pristine, invalid }) => (
            <form onSubmit={handleSubmit}>
              <LoginBox>
                <Flex width={600} flexDirection="row">
                  <label>Email</label>
                  <Field
                    type="email"
                    name="email"
                    component={TextFieldAdapter}
                    placeholder="user@reus.com"
                  />
                </Flex>
                <Flex width={600} flexDirection="row">
                  <label>Password</label>
                  <Field
                    type="password"
                    name="password"
                    component={TextFieldAdapter}
                    placeholder="Password"
                  />
                </Flex>
                <Button px={40} py={15} type="submit" disabled={pristine || invalid}>
                  Sign in
                </Button>
              </LoginBox>
            </form>
          )}
        />
      </Flex>
    </div>
  </div>
);

export default LoginForm;

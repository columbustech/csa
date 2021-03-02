import React from 'react';
import Cookies from 'universal-cookie';
import axios from 'axios';
import { Link } from 'react-router-dom';
import CDrivePathSelector from './CDrivePathSelector';
import './Styles.css';

class JobStatus extends React.Component{
  constructor(props) {
    super(props);
    this.state = {
      job: null,
      actionMessage: ""
    };
    this.pollStatus = this.pollStatus.bind(this);
  }
  pollStatus() {
    const request = axios({
      method: 'GET',
      url: `${this.props.specs.cdriveUrl}app/${this.props.specs.username}/csa/api/status/?uid=${this.props.match.params.uid}`
    });
    request.then(
      response => {
        if (response.data.status === "Running") {
          setTimeout(() => this.pollStatus(), 1000);
        }
        this.setState({
          job: response.data
        });
      },
    );
  }
  render() {
    if (!this.state.job) {
      this.pollStatus();
      return(null);
    } else {
      let actions;
      actions = [];
      if (this.state.job.status === "Running") {
        actions.push(
          <Link className="btn btn-secondary btn-lg mx-3" to="/">
            Cancel
          </Link>
        );
      } else if (this.state.job.status === "Complete" || this.state.job.status === "Error") {
        actions.push(
          <a className="btn btn-primary btn-lg mx-3" href={this.props.specs.appUrl}>
            Finish
          </a>
        );
      }
      let menuButtons = [];
      menuButtons.push(
        <a href={this.props.specs.cdriveUrl} className="btn app-menu-btn">
          Quit
        </a>
      );
      return(
        <div className="app-page">
          <div className="app-header">
            <div className="app-menu">
              {menuButtons}
            </div>
            <div className="app-header-title">
              {"Cloud Data Processor: Split and Apply"}
            </div>
          </div>
          <div className="app-body">
            <div className="app-content">
              <div className="my-5 h3 text-center">
                {"CSA Status"}
              </div>
              <div className="my-4" style={{width: 700}}>
                <span className="mx-2 h5 font-weight-normal">Stage: {this.state.job.stage}</span>
              </div>
              <div className="my-4" style={{width: 700}}>
                <span className="mx-2 h5 font-weight-normal">Status: {this.state.job.long_status}</span>
              </div>
              <div className="my-5 text-center">
                {actions}
              </div>
            </div>
          </div>
        </div>
      );
    }
  }
}

export default JobStatus;

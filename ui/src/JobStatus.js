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
      actionMessage: "",
      statusHtml: ""
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
        let items, statusHtml;
        items = JSON.parse(response.data.long_status);
        statusHtml = items.map(item => {
          return (
            <div style={{width: 700}}>
              <span className="mx-2 h5 font-weight-normal">{item}</span>
            </div>
          );
        });
        this.setState({
          job: response.data,
          statusHtml: statusHtml
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
            Finish Job
          </a>
        );
        actions.push(
          <a className="btn btn-secondary btn-lg mx-3" href={this.props.specs.cdriveUrl}>
            Quit CSA
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
            <div className="cdapp-header-1">
              {"CSA"}
            </div>
            <div className="cdapp-header-2">
              {"Executing Split and Apply Operations on Your Data"}
            </div>
          </div>
          <div className="app-body">
            <div className="app-content">
              {this.state.statusHtml}
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

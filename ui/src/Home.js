import React from 'react';
import Cookies from 'universal-cookie';
import axios from 'axios';
import { Redirect } from 'react-router-dom';
import CDrivePathSelector from './CDrivePathSelector';
import './Styles.css';

class Home extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      uid: "",
      driveObjects: [],
      inputPath: "",
      outputPath: "",
      splitContainer: "",
      applyContainer: "",
      inputPathSelector: false,
      outputPathSelector: false,
      copies: ""
    }
    this.getDriveObjects = this.getDriveObjects.bind(this);
    this.executeJob = this.executeJob.bind(this);
  }
  componentDidMount() {
    this.getDriveObjects();
  }
  getDriveObjects() {
    if(!this.props.specs) {
      return(null);
    }
    const cookies = new Cookies();
    var auth_header = 'Bearer ' + cookies.get('cdp_sa_token');
    const request = axios({
      method: 'GET',
      url: this.props.specs.cdriveApiUrl + "list-recursive/?path=users",
      headers: {'Authorization': auth_header}
    });
    request.then(
      response => {
        this.setState({
          driveObjects: response.data.driveObjects,
        });
      }, err => {
        if(err.response.status === 401) {
          cookies.remove('cdp_sa_token');
          window.location.reload(false);
        } else {
        }
      }
    );
  }
  executeJob() {
    const cookies = new Cookies();
    const request = axios({
      method: 'POST',
      url: `${this.props.specs.appUrl}api/execute/`,
      data: {
        inputPath: this.state.inputPath,
        outputPath: this.state.outputPath,
        splitContainer: this.state.splitContainer,
        applyContainer: this.state.applyContainer,
        copies: this.state.copies
      }
      ,
      headers: {
        'Authorization': `Bearer ${cookies.get('cdp_sa_token')}`,
      }
    });
    request.then(
      response => {
        this.setState({uid: response.data.uid});
      }, err => {
      }
    );
  }
  render() {
    if (this.state.uid !== "") {
      return <Redirect to={`/job/${this.state.uid}/`} />
    } else {
      console.log("reached here");
      let menuButtons = [];
      menuButtons.push(
        <a href={this.props.specs.cdriveUrl} className="btn app-menu-btn">
          Quit
        </a>
      );
      let appBody;
      appBody = (
        <div className="app-content">
          <table className="mx-auto">
            <tr>
              <td>
                <input type="text" className="cdrive-path-input my-3 px-3 no-right-border" placeholder="Input folder" 
                  value={this.state.inputPath} onChange={e => this.setState({inputPath: e.target.value})} />
                <button className="browse-button my-3" onClick={() => this.setState({inputPathSelector: true})}>
                  {"Browse"}
                </button>
              </td>
            </tr>
            <tr>
              <td>
                <input type="text" className="cdrive-path-input my-3 px-3 no-right-border" placeholder="Output file" 
                  value={this.state.outputPath} onChange={e => this.setState({outputPath: e.target.value})} />
                <button className="browse-button my-3" onClick={() => this.setState({outputPathSelector: true})}>
                  {"Browse"}
                </button>
              </td>
            </tr>
            <tr>
              <td>
                <input type="text" className="cdrive-path-input my-3 px-3" placeholder="Split container URL" 
                  value={this.state.splitContainer} onChange={e => this.setState({splitContainer: e.target.value})} />
              </td>
            </tr>
            <tr>
              <td>
                <input type="text" className="cdrive-path-input my-3 px-3" placeholder="Apply container URL" 
                  value={this.state.applyContainer} onChange={e => this.setState({applyContainer: e.target.value})} />
              </td>
            </tr>
            <tr>
              <td>
                <input type="text" className="cdrive-path-input my-3 px-3" placeholder="Apply container copies" 
                  value={this.state.copies} onChange={e => this.setState({copies: e.target.value})} />
              </td>
            </tr>
            <tr>
              <td>
                <div className="w-100 my-4 text-center">
                  <button className="btn btn-primary btn-lg" style={{width: 200}} onClick={this.executeJob}>
                    {"Next"}
                  </button>
                </div>
              </td>
            </tr>
          </table>
          <CDrivePathSelector show={this.state.inputPathSelector} toggle={() => this.setState({inputPathSelector : false})}
            action={path => this.setState({inputPath: path})} title="Select Input Folder"  actionName="Select this folder"
            driveObjects={this.state.driveObjects} type="folder" />
          <CDrivePathSelector show={this.state.outputPathSelector} toggle={() => this.setState({outputPathSelector : false})}
            action={path => this.setState({outputPath: path})} title="Select Output Folder"  actionName="Select this folder"
            driveObjects={this.state.driveObjects} type="folder" />
        </div>
      );
      return (
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
            {appBody}
          </div>
        </div>
      );
    }
  }
}

export default Home;

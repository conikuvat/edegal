'use strict';

// polyfills
import 'whatwg-fetch';

import ko from 'knockout';
import page from 'page';

import MainViewModel from './viewmodels/MainViewModel';


ko.applyBindings(new MainViewModel());
page();

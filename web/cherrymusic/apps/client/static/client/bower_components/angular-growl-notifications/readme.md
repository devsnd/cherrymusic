![AngularJS Growl Notifications](http://i.imgur.com/F4ttQxo.png)

# Growl notifications for AngularJS
[![Build Status](https://travis-ci.org/jvandemo/angular-growl-notifications.png?branch=master)](https://travis-ci.org/jvandemo/angular-growl-notifications)

Notifications logically belong inside the view layer of your application.

Most existing growl systems require you to add notifications using JavaScript inside your controller layer.

This very lightweight library (<2KB) allows you to declaratively create notifications using directives only, supporting both inline expressions and HTML.

Think Growl, but in AngularJS directives. Oh, and Bootstrap compatible too.

- [Visit the official website](http://jvandemo.github.io/angular-growl-notifications/)
- [View live examples](http://jvandemo.github.io/angular-growl-notifications/examples/)
- [Read the complete documentation](http://jvandemo.github.io/angular-growl-notifications/docs/)

[![Official website](http://i.imgur.com/tB1FvX7.png)](http://jvandemo.github.io/angular-growl-notifications/)

# Quick start

Learn how to create Mac OS X like pop-up notifications in your AngularJS application.

### STEP 1: Install the library

Download the code from [GitHub](https://github.com/jvandemo/angular-growl-notifications) or install it using bower:

```sh
$ bower install angular-growl-notifications
```

Load the library in your markup:

```html
<script type="text/javascript" src="angular.js"></script>
<script type="text/javascript" src="angular-growl-notifications.js"></script>
```

Load the `growlNotifications` module in your AngularJS application:

```javascript
angular.module('yourApp', ['growlNotifications']);
```

The library is now loaded in your AngularJS application.

### STEP 2: Specify where you want to render the notifications

Before you can create notifications, you need to add the `growl-notifications` (plural) directive to your markup.

This directive allows you to control where the notifications are rendered in your DOM in case your application requires special behavior.

In most cases you should simply add it as the first element inside the `body` element:

```html
<body>
  <growl-notifications></growl-notifications>

  ...
</body>
```

Check out the [growl-notifications directive documentation](http://jvandemo.github.io/angular-growl-notifications/docs/directives/growl-notifications) for more information.

### STEP 3: Create notifications

You can now use the `growl-notification` (singular) directive to create notifications anywhere in your application:

```html
<!-- This notification will be shown when the page loads -->
<growl-notification>
  Hello world
</growl-notification>
```

Most of the time you will want to show a notification when some event occurs. You can use the native AngularJS `ng-if` directive to make this happen:

```html
<!-- This notification will be shown when showNotification becomes truthy -->
<growl-notification ng-if="showNotification">
  showNotification just became truthy
</growl-notification>
```

By default notifications are shown for 5 seconds, but you can specify the `ttl` in milliseconds for every notification individually:

```html
<growl-notification ttl="1000">
  Only show me for 1000ms
</growl-notification>
```

You can also specify handlers you wish to run when the notification opens and closes:

```html
<growl-notification on-open="doSomething()" on-close="doSomethingElse()">
  ...
</growl-notification>
```

which is convenient if you want to auto-reset some state when the notification is closed:

```html
<button ng-click="showNotification = true">Show notification</button>

<!-- reset showNotification to false again when notification is closed -->
<!-- so the ng-if is triggered every time the button is clicked -->
<growl-notification ng-if="showNotification" on-close="showNotification = false">
  ...
</growl-notification>
```

Check out the [growl-notification directive documentation](http://jvandemo.github.io/angular-growl-notifications/docs/directives/growl-notification) for all available options.

### STEP 4: Customize look and feel

By default no styling is applied so you can completely control the look and feel of the notifications in your application's stylesheet.

The possibilities are endless, for example to display notifications in the top right of your page:

```css
growl-notifications{
  position: fixed;
  top: 150px;
  right: 10px;
}
growl-notification{
  border: 1px solid black;
  padding: 15px 30px;
  margin-bottom: 15px;
}
```

### That's it

![Hello world](http://i.imgur.com/T4Z2KPj.gif)

You now have a working notification system in your AngularJS application.

When you load the page, a "Hello world" notification will automatically appear and disappear.

There are many additional features and options, so make sure to visit the [examples page](http://jvandemo.github.io/angular-growl-notifications/examples) for more inspiration and sample code.

## License

MIT

## Change log

### v2.2.0

- Added support for `on-open` handler
- Added support for `on-close` handler
- Updated documentation

### v2.1.2

- Make angular dependency version less strict

### v2.1.1

- Fix issue with injection of `$animate` in controller of `growlNotification` directive

### v2.1.0

- Update code to follow the [AngularJS styleguide](https://github.com/toddmotto/angularjs-styleguide) principles

### v2.0.1

- Fix issue with minification of controller in `growlNotification` directive (see [this issue](https://github.com/jvandemo/angular-growl-notifications/issues/3)).

### v2.0.0

- Directives have been rewritten for better performance
- Now supports manually closing notifications using markup
- v1 release has been moved to v1.x.x branch

### v0.7.0

- Added support for custom css prefix (defaults to Bootstrap alert)

### v0.6.0

- The growl-notifications directive now uses an isolate scope

### v0.5.0

- Added support for custom options in growl-notification directive
- Updated demo page

### v0.4.0

- Added $animate support
- Updated demo page

### v0.3.0

- Added dist directory with pre-built library files
- Added demo page

### v0.2.0

- Added `growl-notification` directive to conveniently add notifications from within HTML markup
- Added `growl-notifications` directive to conveniently display notifications from within HTML markup
- Added documentation

### v0.1.0

- Initial version

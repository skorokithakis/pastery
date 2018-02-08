terraform {
  backend "s3" {
    bucket = "terraformstate.stochastic.io"
    key    = "pastery/terraform.tfstate"
    region = "eu-central-1"
  }
}

variable "cloudflare_email" {}
variable "cloudflare_token" {}

variable ipv6_ip { default = "2001:19f0:5:fc8:5400:ff:fe7d:1191" }
variable ipv4_ip { default = "45.63.15.100" }
variable domain { default = "pastery.net" }

provider "cloudflare" {
  email = "${var.cloudflare_email}"
  token = "${var.cloudflare_token}"
}

resource "cloudflare_record" "v6_root" {
  domain="${var.domain}"
  type="AAAA"
  name="@"
  proxied="true"
  value="${var.ipv6_ip}"
}

resource "cloudflare_record" "v6_www" {
  name="www"
  domain="${var.domain}"
  type="AAAA"
  proxied="true"
  value="${var.ipv6_ip}"
}

resource "cloudflare_record" "root" {
  name="@"
  domain="${var.domain}"
  type="A"
  proxied="true"
  value="${var.ipv4_ip}"
}

resource "cloudflare_record" "www" {
  name="www"
  domain="${var.domain}"
  type="A"
  proxied="true"
  value="${var.ipv4_ip}"
}

resource "cloudflare_record" "email" {
  name="email"
  domain="${var.domain}"
  type="CNAME"
  value="u6640409.wl160.sendgrid.net"
}

resource "cloudflare_record" "s1_domainkey" {
  domain="${var.domain}"
  type="CNAME"
  name="s1._domainkey"
  value="s1.domainkey.u6640409.wl160.sendgrid.net"
}

resource "cloudflare_record" "s2_domainkey" {
  domain="${var.domain}"
  type="CNAME"
  name="s2._domainkey"
  value="s2.domainkey.u6640409.wl160.sendgrid.net"
}

resource "cloudflare_record" "mx10" {
  domain="${var.domain}"
  type="MX"
  name="@"
  priority="10"
  value="mxa.mailgun.com"
}

resource "cloudflare_record" "mx20" {
  domain="${var.domain}"
  type="MX"
  name="@"
  priority="20"
  value="mxb.mailgun.com"
}

resource "cloudflare_record" "domainkey" {
  domain="${var.domain}"
  type="TXT"
  name="mailo._domainkey"
  value="k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC1GtC1uRq7aiVPHZVNZU9eP+o93naS0f/dw5Ojof/c7VZtYioHwyS7psQeTgt50MX0JuyxQvfGryg7mFygRI4qsoTsdfLPM00hEYdBIsn+7x1UMRcsg/he6+8dnYhADwCJv/4HBC8znlRNb1kkP3u2zVaaq73fG0i/Pe25ES5szQIDAQAB"
}

resource "cloudflare_record" "googlesite1" {
  domain="${var.domain}"
  type="TXT"
  name="@"
  value="google-site-verification=jQgHBNQhJhenKMX4WJLSEQG3g9K_xp4NhSvo8Xwi5xE"
}

resource "cloudflare_record" "googlesite2" {
  domain="${var.domain}"
  type="TXT"
  name="@"
  value="google-site-verification=lM1Ik9f3lH9BUWpPLNNa7AQHSUGqo-sD-r-oBd1moJU"
}

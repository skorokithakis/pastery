terraform {
  backend "http" {
  }
}

terraform {
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 2.0"
    }
  }
}

provider "cloudflare" {
  api_token = var.cloudflare_token
}


variable "cloudflare_token" {}
variable "zone_id" {
  default = "f1928f8f37c9e76fc7c99a7cc9455702"
}

variable ipv6_ip { default = "2a01:4f8:1c0c:6109::1" }
variable ipv4_ip { default = "195.201.40.251" }
variable domain { default = "pastery.net" }

resource "cloudflare_record" "v6_root" {
  zone_id = var.zone_id
  type    = "AAAA"
  name    = "@"
  proxied = "true"
  value   = var.ipv6_ip
}

resource "cloudflare_record" "v6_www" {
  name    = "www"
  zone_id = var.zone_id
  type    = "AAAA"
  proxied = "true"
  value   = var.ipv6_ip
}

resource "cloudflare_record" "root" {
  name    = "@"
  zone_id = var.zone_id
  type    = "A"
  proxied = "true"
  value   = var.ipv4_ip
}

resource "cloudflare_record" "www" {
  name    = "www"
  zone_id = var.zone_id
  type    = "A"
  proxied = "true"
  value   = var.ipv4_ip
}

resource "cloudflare_record" "email" {
  name    = "email"
  zone_id = var.zone_id
  type    = "CNAME"
  value   = "u6640409.wl160.sendgrid.net"
}

resource "cloudflare_record" "s1_domainkey" {
  zone_id = var.zone_id
  type    = "CNAME"
  name    = "s1._domainkey"
  value   = "s1.domainkey.u6640409.wl160.sendgrid.net"
}

resource "cloudflare_record" "s2_domainkey" {
  zone_id = var.zone_id
  type    = "CNAME"
  name    = "s2._domainkey"
  value   = "s2.domainkey.u6640409.wl160.sendgrid.net"
}

resource "cloudflare_record" "mx10" {
  zone_id  = var.zone_id
  type     = "MX"
  name     = "@"
  priority = "10"
  value    = "mxa.mailgun.org"
}

resource "cloudflare_record" "mx20" {
  zone_id  = var.zone_id
  type     = "MX"
  name     = "@"
  priority = "20"
  value    = "mxb.mailgun.org"
}

resource "cloudflare_record" "domainkey" {
  zone_id = var.zone_id
  type    = "TXT"
  name    = "mailo._domainkey"
  value   = "k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC1GtC1uRq7aiVPHZVNZU9eP+o93naS0f/dw5Ojof/c7VZtYioHwyS7psQeTgt50MX0JuyxQvfGryg7mFygRI4qsoTsdfLPM00hEYdBIsn+7x1UMRcsg/he6+8dnYhADwCJv/4HBC8znlRNb1kkP3u2zVaaq73fG0i/Pe25ES5szQIDAQAB"
}

resource "cloudflare_record" "googlesite1" {
  zone_id = var.zone_id
  type    = "TXT"
  name    = "@"
  value   = "google-site-verification=jQgHBNQhJhenKMX4WJLSEQG3g9K_xp4NhSvo8Xwi5xE"
}

resource "cloudflare_record" "googlesite2" {
  zone_id = var.zone_id
  type    = "TXT"
  name    = "@"
  value   = "google-site-verification=lM1Ik9f3lH9BUWpPLNNa7AQHSUGqo-sD-r-oBd1moJU"
}

resource "cloudflare_record" "brave_verification" {
  zone_id = var.zone_id
  type    = "TXT"
  name    = "@"
  value   = "brave-ledger-verification=46645759d1b66f771d031329b11c976a41830103bbfc3f07d53d447a7305c22b"
}


resource "cloudflare_filter" "filter_eastern_europe" {
  expression = "ip.geoip.country eq \"RU\" or ip.geoip.country eq \"UZ\" or ip.geoip.country eq \"UA\" or ip.geoip.country eq \"BY\""
  paused = false
  zone_id = var.zone_id
}

resource "cloudflare_firewall_rule" "block_eastern_europe" {
  action = "js_challenge"
  description = "Block Eastern Europe"
  filter_id = cloudflare_filter.filter_eastern_europe.id
  paused = false
  zone_id = var.zone_id
}

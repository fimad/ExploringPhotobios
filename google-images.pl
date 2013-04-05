#!/usr/bin/perl
use warnings;
use strict;
use URI;
use Web::Scraper;
use Getopt::Long;

################################################################################
# Command Line arguments
################################################################################

my $_QUERY;
my $_OUTPUT;
my $_MAX=100;

GetOptions(
        "query=s"   =>  \$_QUERY
    ,   "output=s"  =>  \$_OUTPUT
    ,   "max=i"     =>  \$_MAX
);

die("usage: $0 -q 'search query' -o 'output' -m 100\n")
if not defined $_QUERY
or not defined $_OUTPUT;

################################################################################
# Web scraper defines
################################################################################

my $imageSearch = scraper {
    process 'table.images_table > tr > td > a', "images[]" => '@href';
};

################################################################################
# Main
################################################################################

my $page = 0;
my $total = 0;
my $outOfImages = 0;

while( !$outOfImages and $total<$_MAX ){
    my $results = $imageSearch->scrape(URI->new("http://www.google.com/search?q=$_QUERY&hl=en&biw=1920&bih=1064&gbv=2&tbm=isch&sout=1&start=$page"));

    my $oldTotal = $total;
    for my $image (@{$results->{images}}){
        if( $image =~ m/imgurl=(.+)\&imgrefurl=/ ){
#        print "url: $1\n";
            my $url = $1;
            print ".";
            `wget --no-check-certificate -P $_OUTPUT '$url' 2> /dev/null > /dev/null`;
            $total += 1;
        }
    }

    $outOfImages = 1 if $total == $oldTotal;
    $page += 20;
    sleep(1);
    print "\n";
}

